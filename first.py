import streamlit as st
import requests
import os
from langdetect import detect
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# API Keys
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
DID_API_KEY = os.getenv("DID_API_KEY")

if not ELEVENLABS_API_KEY or not DID_API_KEY:
    st.error("❌ Missing API keys. Check your .env file.")
    st.stop()

# ----------------- LANGUAGE DETECTION -----------------
def detect_language(text):
    try:
        return detect(text)
    except Exception as e:
        st.error(f"Language detection failed: {e}")
        return None

# ----------------- AUDIO GENERATION -----------------
def generate_audio(text, voice_id):
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1"
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        audio_path = "output_audio.mp3"
        with open(audio_path, "wb") as f:
            f.write(response.content)
        return audio_path
    except Exception as e:
        st.error(f"🎧 Audio generation error: {e}")
        return None

# ----------------- IMAGE UPLOAD -----------------
def upload_image(image_path):
    headers = {"Authorization": f"Bearer {DID_API_KEY}"}
    with open(image_path, "rb") as img_file:
        response = requests.post(
            "https://api.d-id.com/images",
            headers=headers,
            files={"image": img_file}
        )
    if response.status_code != 200:
        st.error(f"Image upload failed: {response.text}")
        return None
    return response.json().get("url")

# ----------------- AUDIO UPLOAD -----------------
def upload_audio(audio_path):
    headers = {"Authorization": f"Bearer {DID_API_KEY}"}
    with open(audio_path, "rb") as audio_file:
        response = requests.post(
            "https://api.d-id.com/audio",
            headers=headers,
            files={"audio": audio_file}
        )
    if response.status_code != 200:
        st.error(f"Audio upload failed: {response.text}")
        return None
    return response.json().get("url")

# ----------------- VIDEO GENERATION WITH POLLING -----------------
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
        st.error(f"Video creation failed: {response.text}")
        return None

    video_id = response.json().get("id")
    if not video_id:
        st.error("No video ID received from D-ID.")
        return None

    # Poll for video status (up to ~40 seconds)
    for _ in range(20):
        time.sleep(2)
        status_resp = requests.get(
            f"https://api.d-id.com/talks/{video_id}",
            headers={"Authorization": f"Bearer {DID_API_KEY}"}
        )
        if status_resp.status_code != 200:
            st.error(f"Failed to get video status: {status_resp.text}")
            return None

        status_json = status_resp.json()
        status = status_json.get("status")
        if status == "done":
            return status_json.get("result_url") or status_json.get("video_url")
        elif status == "failed":
            st.error("Video generation failed on server.")
            return None
        # If status is still processing, continue polling

    st.error("Timed out waiting for video generation.")
    return None

# ----------------- MAIN APP -----------------
def main():
    st.title("🗞️ AI News Reader (ElevenLabs + D-ID)")
    st.write("Paste any news text. Get an AI video reader with voice & lipsync animation.")

    text = st.text_area("📜 Paste your news content here", height=200)
    voice_choice = st.radio("🎤 Choose Voice", ["Male", "Female"])
    target_lang = st.selectbox("🌐 Output Language (future use)", ["en", "hi", "te", "ta", "es", "fr", "de"])

    if st.button("🚀 Generate AI Video"):
        if not text.strip():
            st.error("❌ Please paste some news content.")
            return

        lang = detect_language(text)
        if not lang:
            return
        st.success(f"✅ Detected Language: `{lang}`")

        st.warning("⚠️ Translation not applied in this version.")
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

        image_path = "reader.jpeg"  # <-- Updated from reader.jpg to reader.jpeg
        if not os.path.exists(image_path):
            st.error(f"❌ '{image_path}' image not found in project folder.")
            return

        st.info("Uploading image...")
        image_url = upload_image(image_path)
        if not image_url:
            return
        st.info(f"Image uploaded: {image_url}")

        st.info("Uploading audio...")
        audio_url = upload_audio(audio_path)
        if not audio_url:
            return
        st.info(f"Audio uploaded: {audio_url}")

        st.info("Generating video (this may take up to 30 seconds)...")
        video_url = generate_video(image_url, audio_url)
        if video_url:
            st.video(video_url)
        else:
            st.error("❌ Failed to generate video. Check API key or usage limits.")

if __name__ == "__main__":
    main()
