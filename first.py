import streamlit as st
import requests
import os
from langdetect import detect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
DID_API_KEY = os.getenv("DID_API_KEY")

# Validate API keys
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

# ----------------- VIDEO GENERATION USING D-ID -----------------
def generate_video(image_path, audio_path):
    try:
        headers = {
            "Authorization": f"Bearer {DID_API_KEY}"
        }

        # Upload image
        with open(image_path, "rb") as img_file:
            image_upload = requests.post(
                "https://api.d-id.com/images",
                headers=headers,
                files={"image": img_file}
            )
        if image_upload.status_code == 401:
            st.error("❌ Unauthorized: Invalid or expired D-ID API key.")
            return None
        image_upload.raise_for_status()
        image_url = image_upload.json().get("url")

        # Upload audio
        with open(audio_path, "rb") as audio_file:
            audio_upload = requests.post(
                "https://api.d-id.com/audio",
                headers=headers,
                files={"audio": audio_file}
            )
        audio_upload.raise_for_status()
        audio_url = audio_upload.json().get("url")

        # Create video
        payload = {
            "image_url": image_url,
            "audio_url": audio_url,
            "driver_url": "default",
            "config": {
                "fluent": True,
                "align_driver": True
            }
        }

        video_response = requests.post(
            "https://api.d-id.com/talks",
            headers={**headers, "Content-Type": "application/json"},
            json=payload
        )
        video_response.raise_for_status()
        video_id = video_response.json().get("id")
        return f"https://api.d-id.com/talks/{video_id}/video"

    except Exception as e:
        st.error(f"🎬 Video generation failed: {e}")
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

        # Step 1: Detect language
        lang = detect_language(text)
        if not lang:
            return
        st.success(f"✅ Detected Language: `{lang}`")

        # Step 2: Translation placeholder
        st.warning("⚠️ Translation not applied in this version.")
        final_text = text

        # Step 3: Choose voice
        voice_map = {
            "Male": "pNInz6obpgDQGcFmaJgB",
            "Female": "21m00Tcm4TlvDq8ikWAM"
        }
        voice_id = voice_map[voice_choice]

        # Step 4: Generate Audio
        audio_path = generate_audio(final_text, voice_id)
        if not audio_path:
            return
        st.audio(audio_path, format="audio/mp3")

        # Step 5: Check image file
        image_path = "reader.jpeg"
        if not os.path.exists(image_path):
            st.error("❌ 'reader.jpg' image not found in project folder.")
            return

        # Step 6: Generate Video
        video_url = generate_video(image_path, audio_path)
        if video_url:
            st.video(video_url)
        else:
            st.error("❌ Failed to generate video. Check API key or usage limits.")

if __name__ == "__main__":
    main()
