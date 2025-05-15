import streamlit as st
import requests
import os
from langdetect import detect
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
DID_API_KEY = os.getenv("DID_API_KEY")

st.write(f"ELEVENLABS_API_KEY loaded? {'Yes' if ELEVENLABS_API_KEY else 'No'}")
st.write(f"DID_API_KEY loaded? {'Yes' if DID_API_KEY else 'No'}")

if not ELEVENLABS_API_KEY or not DID_API_KEY:
    st.error("❌ Missing API keys. Please check your .env file.")
    st.stop()

def detect_language(text):
    try:
        return detect(text)
    except Exception as e:
        st.error(f"Language detection error: {e}")
        return None

def generate_audio(text, voice_id):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1"
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        audio_path = "output_audio.mp3"
        with open(audio_path, "wb") as f:
            f.write(response.content)
        return audio_path
    except Exception as e:
        st.error(f"Audio generation failed: {e}")
        return None

def upload_image(image_path):
    st.write(f"Uploading image with DID_API_KEY: {DID_API_KEY[:5]}...")
    headers = {"Authorization": f"Bearer {DID_API_KEY}"}
    with open(image_path, "rb") as img_file:
        files = {"image": ("reader.jpeg", img_file, "image/jpeg")}
        response = requests.post(
            "https://api.d-id.com/images",
            headers=headers,
            files=files
        )
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        st.error(f"Image upload failed: {response.status_code} {response.text}")
        return None
    json_resp = response.json()
    st.write(f"Image upload response: {json_resp}")
    return json_resp.get("url")

def upload_audio(audio_path):
    st.write(f"Uploading audio with DID_API_KEY: {DID_API_KEY[:5]}...")
    headers = {"Authorization": f"Bearer {DID_API_KEY}"}
    with open(audio_path, "rb") as audio_file:
        files = {"audio": ("output_audio.mp3", audio_file, "audio/mpeg")}
        response = requests.post(
            "https://api.d-id.com/audio",
            headers=headers,
            files=files
        )
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        st.error(f"Audio upload failed: {response.status_code} {response.text}")
        return None
    json_resp = response.json()
    st.write(f"Audio upload response: {json_resp}")
    return json_resp.get("url")

def generate_video(image_url, audio_url):
    headers = {
        "Authorization": f"Bearer {DID_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "image_url": image_url,
        "audio_url": audio_url,
        "driver_url": "default",
        "config": {
            "fluent": True,
            "align_driver": True
        }
    }
    response = requests.post(
        "https://api.d-id.com/talks",
        headers=headers,
        json=payload
    )
    if response.status_code != 201:
        st.error(f"Video creation failed: {response.status_code} {response.text}")
        return None

    video_id = response.json().get("id")
    if not video_id:
        st.error("No video ID received from D-ID API.")
        return None

    st.info("Waiting for video generation (up to 40 seconds)...")
    for _ in range(20):
        time.sleep(2)
        status_resp = requests.get(
            f"https://api.d-id.com/talks/{video_id}",
            headers={"Authorization": f"Bearer {DID_API_KEY}"}
        )
        if status_resp.status_code != 200:
            st.error(f"Failed to get video status: {status_resp.status_code} {status_resp.text}")
            return None
        status_json = status_resp.json()
        status = status_json.get("status")
        if status == "done":
            return status_json.get("result_url") or status_json.get("video_url")
        elif status == "failed":
            st.error("Video generation failed on server.")
            return None
    st.error("Timed out waiting for video generation.")
    return None

def main():
    st.title("🗞️ AI News Reader (ElevenLabs + D-ID)")
    st.write("Paste news text, generate an AI video with voice and lip-sync.")

    text = st.text_area("Paste your news here", height=200)
    voice_choice = st.radio("Choose voice", ["Male", "Female"])

    if st.button("Generate AI Video"):
        if not text.strip():
            st.error("Please enter some text.")
            return

        lang = detect_language(text)
        if not lang:
            return
        st.success(f"Detected language: {lang}")

        # Skipping translation for now, you can add it later
        final_text = text

        voice_map = {
            "Male": "pNInz6obpgDQGcFmaJgB",
            "Female": "21m00Tcm4TlvDq8ikWAM"
        }
        voice_id = voice_map[voice_choice]

        audio_path = generate_audio(final_text, voice_id)
        if not audio_path:
            return
        st.audio(audio_path, format="audio/mp3")

        image_path = "reader.jpeg"  # Make sure this file exists in your app folder
        if not os.path.exists(image_path):
            st.error(f"Image file '{image_path}' not found in your folder.")
            return

        image_url = upload_image(image_path)
        if not image_url:
            return

        audio_url = upload_audio(audio_path)
        if not audio_url:
            return

        video_url = generate_video(image_url, audio_url)
        if video_url:
            st.video(video_url)
        else:
            st.error("Failed to generate video.")

if __name__ == "__main__":
    main()
