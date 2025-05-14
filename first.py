
import streamlit as st
import requests
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
import subprocess
import os
import json
from dotenv import load_dotenv
from google.auth.exceptions import DefaultCredentialsError

# Load environment variables
load_dotenv()

# Load credentials from env variable
google_credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
DID_API_KEY = os.getenv("DID_API_KEY")

# Build Google Translate client
def get_translate_client():
    try:
        creds_dict = json.loads(google_credentials_json)
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        return translate.Client(credentials=creds)
    except Exception as e:
        st.error(f"Failed to create Google Translate client: {e}")
        return None

# Language detection
def detect_language(text):
    client = get_translate_client()
    if not client:
        return None
    try:
        result = client.detect_language(text)
        return result["language"]
    except Exception as e:
        st.error(f"Error detecting language: {e}")
        return None

# Translation
def translate_text(text, target_language):
    client = get_translate_client()
    if not client:
        return None
    try:
        result = client.translate(text, target_language=target_language)
        return result["translatedText"]
    except Exception as e:
        st.error(f"Error translating text: {e}")
        return None

# ElevenLabs TTS
def generate_audio(text, voice="male"):
    try:
        url = "https://api.elevenlabs.io/generate"
        headers = {"Authorization": f"Bearer {ELEVENLABS_API_KEY}"}
        payload = {"voice": voice, "text": text}
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json().get("audio_url")
    except Exception as e:
        st.error(f"Audio generation failed: {e}")
        return None

# Wav2Lip (optional if using D-ID)
def sync_lips(audio_file, image_file):
    try:
        subprocess.run(["python", "Wav2Lip.py", "--audio", audio_file, "--image", image_file], check=True)
    except Exception as e:
        st.error(f"Lip sync failed: {e}")

# D-ID Video
def generate_video_with_did(image_file, audio_file):
    try:
        api_url = "https://api.d-id.com/animate"
        headers = {"Authorization": f"Bearer {DID_API_KEY}"}
        files = {'image': open(image_file, 'rb'), 'audio': open(audio_file, 'rb')}
        response = requests.post(api_url, headers=headers, files=files)
        response.raise_for_status()
        return response.json().get("video_url")
    except Exception as e:
        st.error(f"Video generation failed: {e}")
        return None

# Streamlit App
def app():
    st.title("🗞️ AI News Reader")

    text_input = st.text_area("Paste your news content here")
    language = st.selectbox("Choose Output Language", ["en", "es", "fr", "de"])
    voice = st.radio("Choose Voice", ["Male", "Female"])

    if st.button("Generate News Video"):
        if not text_input.strip():
            st.error("Please enter news content.")
            return

        detected_language = detect_language(text_input)
        if not detected_language:
            return
        st.success(f"Detected Language: {detected_language}")

        # Translate if needed
        translated_text = text_input if detected_language == language else translate_text(text_input, target_language=language)
        if not translated_text:
            return
        st.write("Translated Text:", translated_text)

        # Generate audio
        audio_url = generate_audio(translated_text, voice="male" if voice == "Male" else "female")
        if not audio_url:
            return
        st.audio(audio_url)

        # Save audio file
        audio_path = "output_audio.mp3"
        with open(audio_path, "wb") as f:
            f.write(requests.get(audio_url).content)

        image_path = "reader.jpg"
        if not os.path.exists(image_path):
            st.error("Reader image not found.")
            return

        video_url = generate_video_with_did(image_path, audio_path)
        if video_url:
            st.video(video_url)
        else:
            st.error("Failed to generate video.")

if __name__ == "__main__":
    app()
