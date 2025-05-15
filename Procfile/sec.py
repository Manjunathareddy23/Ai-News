import streamlit as st
from langdetect import detect
from gtts import gTTS
import os
import requests
import subprocess

st.set_page_config(page_title="AI News Reader", layout="centered")
st.title("🗞️ AI News Reader (Free Version)")

news_text = st.text_area("📜 Paste your news content here")

face_img = st.file_uploader("🖼️ Upload a face image (JPG/PNG)", type=["jpg", "png"])

# Paths
checkpoint_path = "Wav2Lip/checkpoints/wav2lip_gan.pth"
video_path = "results/result_voice.mp4"
model_url = "https://huggingface.co/spaces/akhilpamidi/wav2lip-model/resolve/main/wav2lip_gan.pth"

# Automatically download model if missing
if not os.path.isfile(checkpoint_path):
    st.warning("⚠️ Wav2Lip model not found. Downloading...")
    os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
    try:
        r = requests.get(model_url)
        r.raise_for_status()
        with open(checkpoint_path, 'wb') as f:
            f.write(r.content)
        st.success("✅ Model downloaded successfully!")
    except Exception as e:
        st.error(f"❌ Failed to download model: {e}")
        st.stop()

if st.button("🎬 Generate Video"):
    if news_text and face_img:
        st.success("✅ Starting generation...")

        try:
            lang = detect(news_text)
            st.info(f"🌐 Detected Language: `{lang}`")

            tts = gTTS(text=news_text, lang=lang)
            tts.save("news_audio.mp3")

            with open("input_face.jpg", "wb") as f:
                f.write(face_img.read())

            os.makedirs("results", exist_ok=True)

            # Run Wav2Lip using subprocess for better error capture
            command = [
                "python3", "Wav2Lip/inference.py",
                "--checkpoint_path", checkpoint_path,
                "--face", "input_face.jpg",
                "--audio", "news_audio.mp3"
            ]
            result = subprocess.run(command, capture_output=True, text=True)

            if result.returncode == 0 and os.path.exists(video_path):
                st.success("✅ Video generated successfully!")
                st.video(video_path)
                with open(video_path, "rb") as f:
                    st.download_button("⬇️ Download Video", f, file_name="AI_News.mp4", mime="video/mp4")
            else:
                st.error("❌ Video generation failed.")
                st.text("🔍 Logs:\n" + result.stderr)

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    else:
        st.warning("⚠️ Please input news and upload a face image.")
