import streamlit as st
import requests
import os
from langdetect import detect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API keys from environment variables
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
DID_API_KEY = os.getenv("DID_API_KEY")

# ----------------- LANGUAGE DETECTION -----------------
def detect_language(text):
    try:
        return detect(text)
    except Exception as e:
        st.error(f"Language detection failed: {e}")
        return None

# ----------------- TRANSLATION (Not available in free version) -----------------
def translate_text(text, target_lang):
    st.warning("⚠️ Translation is not available in this free version.")
    return text

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
        st.error(f"Audio generation error: {e}")
        return None

# ----------------- VIDEO GENERATION -----------------
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

# ----------------- STREAMLIT UI -----------------
def main():
    st.title("🗞️ AI News Reader (Free Version)")
    st.write("Paste news content in any language, detect language, and generate a speaking news video.")

    text = st.text_area("📝 Enter news content")
    target_lang = st.selectbox("🌐 Output Language (for future use)", ["en", "es", "fr", "hi", "te", "ta", "de"])
    voice_choice = st.radio("🎤 Voice", ["Male", "Female"])

    if st.button("🎬 Generate Video"):
        if not text.strip():
            st.error("❌ Please enter news content.")
            return

        detected_lang = detect_language(text)
        if not detected_lang:
            return

        st.success(f"✅ Detected Language: `{detected_lang}`")

        translated_text = text  # Translation placeholder
        st.info(f"🔤 Processed Text (No Translation Applied):\n\n{translated_text}")

        # Replace these with your actual voice IDs from ElevenLabs
        voice_map = {
            "Male": "pNInz6obpgDQGcFmaJgB",     # Replace with your ElevenLabs Male voice_id
            "Female": "21m00Tcm4TlvDq8ikWAM"    # Replace with your ElevenLabs Female voice_id
        }

        voice_id = voice_map[voice_choice]
        audio_path = generate_audio(translated_text, voice_id)
        if not audio_path:
            return

        st.audio(audio_path, format="audio/mp3")

        image_path = "reader.jpeg"
        if not os.path.exists(image_path):
            st.error("❌ `reader.jpg` file not found! Please place the image in the same directory.")
            return

        video_url = generate_video(image_path, audio_path)
        if video_url:
            st.video(video_url)
        else:
            st.error("❌ Video generation failed.")

if __name__ == "__main__":
    main()
