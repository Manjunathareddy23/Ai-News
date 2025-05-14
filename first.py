import streamlit as st
import requests
from google.cloud import translate_v2 as translate
import subprocess
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variables
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
DID_API_KEY = os.getenv('DID_API_KEY')

# Google Cloud Language Detection
def detect_language(text):
    client = translate.Client()
    result = client.detect_language(text)
    return result['language']

# Google Cloud Translate Text
def translate_text(text, target_language):
    client = translate.Client()
    result = client.translate(text, target_lang=target_language)
    return result['translatedText']

# ElevenLabs Text-to-Speech (TTS)
def generate_audio(text, voice="male"):
    url = "https://api.elevenlabs.io/generate"
    headers = {"Authorization": f"Bearer {ELEVENLABS_API_KEY}"}
    payload = {
        "voice": voice,
        "text": text
    }
    response = requests.post(url, headers=headers, json=payload)
    audio_url = response.json()["audio_url"]
    return audio_url

# Wav2Lip Integration (or D-ID)
def sync_lips(audio_file, image_file):
    command = ["python", "Wav2Lip.py", "--audio", audio_file, "--image", image_file]
    subprocess.run(command)

# Using D-ID API for Video Generation (Optional)
def generate_video_with_did(image_file, audio_file):
    api_url = "https://api.d-id.com/animate"
    headers = {"Authorization": f"Bearer {DID_API_KEY}"}
    files = {
        'image': open(image_file, 'rb'),
        'audio': open(audio_file, 'rb')
    }
    response = requests.post(api_url, headers=headers, files=files)
    video_url = response.json().get("video_url")
    return video_url

# Streamlit UI
def app():
    st.title("AI News Reader")
    
    # Text input for news content
    text_input = st.text_area("Paste news content")
    
    # Choose language and voice
    language = st.selectbox("Choose Language", ["en", "es", "fr", "de"])  # Add more languages as needed
    voice = st.radio("Choose Voice", ["Male", "Female"])
    
    # Button to generate news video
    if st.button("Generate News Video"):
        if text_input:
            # Language detection
            detected_language = detect_language(text_input)
            st.write(f"Detected Language: {detected_language}")
            
            # Translate text if necessary
            if detected_language != language:
                translated_text = translate_text(text_input, target_language=language)
                st.write(f"Translated Text: {translated_text}")
            else:
                translated_text = text_input

            # Generate audio
            audio_url = generate_audio(translated_text, voice="male" if voice == "Male" else "female")
            st.audio(audio_url)
            
            # Generate video with lip syncing using D-ID (or Wav2Lip)
            image_file = 'IMG_20250426_180320.jpg'  # Set your reader image path
            video_url = generate_video_with_did(image_file, audio_url)
            if video_url:
                st.video(video_url)
            else:
                st.error("Video generation failed. Please try again.")
        else:
            st.error("Please enter news content to proceed.")

if __name__ == "__main__":
    app()
