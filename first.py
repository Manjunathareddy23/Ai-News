import streamlit as st
import requests
import os
import json
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API keys and credentials path from environment variables
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
DID_API_KEY = os.getenv("DID_API_KEY")

def get_translate_client():
    try:
        if not os.path.exists(GOOGLE_CREDENTIALS_PATH):
            st.error(f"Google credentials file not found at {GOOGLE_CREDENTIALS_PATH}. Please check the path.")
            return None
        
        with open(GOOGLE_CREDENTIALS_PATH) as f:
            creds_dict = json.load(f)
        
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        return translate.Client(credentials=creds)
    
    except json.JSONDecodeError:
        st.error("Error decoding the credentials JSON file.")
        return None
    except Exception as e:
        st.error(f"Google Translate client error: {e}")
        return None

def detect_language(text):
    client = get_translate_client()
    if not client:
        return None
    try:
        result = client.detect_language(text)
        return result["language"]
    except Exception as e:
        st.error(f"Language detection failed: {e}")
        return None

def translate_text(text, target):
    client = get_translate_client()
    if not client:
        return None
    try:
        result = client.translate(text, target_language=target)
        return result["translatedText"]
    except Exception as e:
        st.error(f"Translation failed: {e}")
        return None

def generate_audio(text, voice="Rachel"):
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
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
        st.error(f"Audio generation error: {e}")
        return None

def generate_video(image_path, audio_path):
    try:
        with open(image_path, "rb") as img_file, open(audio_path, "rb") as audio_file:
            files = {
                "source_image": img_file,
                "script": ("script.mp3", audio_file, "audio/mpeg")
            }
            headers = {
                "Authorization": f"Bearer {DID_API_KEY}"
            }
            response = requests.post(
                "https://api.d-id.com/talks",
                headers=headers,
                files=files
            )
            response.raise_for_status()
            video_response = response.json()
            return video_response.get("result_url") or video_response.get("video_url")
    except Exception as e:
        st.error(f"Video generation failed: {e}")
        return None

def main():
    st.title("🗞️ AI News Reader")
    st.write("Paste news content in any language, select language and voice, and generate a speaking news video.")

    text = st.text_area("📝 Enter news content")
    target_lang = st.selectbox("🌐 Output Language", ["en", "es", "fr", "hi", "te", "ta", "de"])
    voice_choice = st.radio("🎤 Voice", ["Male", "Female"])

    if st.button("Generate Video"):
        if not text.strip():
            st.error("Please enter news content.")
            return

        detected_lang = detect_language(text)
        if not detected_lang:
            return

        st.success(f"Detected Language: {detected_lang}")

        translated_text = text if detected_lang == target_lang else translate_text(text, target_lang)
        if not translated_text:
            return

        st.write("🔤 Translated Text:")
        st.info(translated_text)

        voice_map = {"Male": "Adam", "Female": "Rachel"}
        audio_path = generate_audio(translated_text, voice=voice_map[voice_choice])
        if not audio_path:
            return

        st.audio(audio_path, format="audio/mp3")

        image_path = "reader.jpg"
        if not os.path.exists(image_path):
            st.error("reader.jpg file not found!")
            return

        video_url = generate_video(image_path, audio_path)
        if video_url:
            st.video(video_url)
        else:
            st.error("Video generation failed.")

if __name__ == "__main__":
    main()
    
