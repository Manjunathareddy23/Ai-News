import streamlit as st
from langdetect import detect
from gtts import gTTS
import os
import requests

st.set_page_config(page_title="AI News Reader", layout="centered")
st.title("🗞️ AI News Reader (Free Version)")

news_text = st.text_area("📜 Paste your news content here")

face_img = st.file_uploader("🖼️ Upload a face image (JPG/PNG)", type=["jpg", "png"])

# Auto-download Wav2Lip model if missing
checkpoint_path = "Wav2Lip/checkpoints/wav2lip_gan.pth"
model_url = "https://huggingface.co/spaces/akhilpamidi/wav2lip-model/resolve/main/wav2lip_gan.pth"

if not os.path.isfile(checkpoint_path):
    st.warning("⚠️ Model file not found. Downloading Wav2Lip model checkpoint...")
    os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
    try:
        r = requests.get(model_url)
        with open(checkpoint_path, 'wb') as f:
            f.write(r.content)
        st.success("✅ Model downloaded successfully!")
    except Exception as e:
        st.error(f"❌ Failed to download model: {e}")
        st.stop()

if st.button("🎬 Generate Video"):
    if news_text and face_img:
        st.success("✅ Processing started...")

        try:
            # Language Detection
            lang = detect(news_text)
            st.info(f"🌐 Detected Language: `{lang}`")

            # Convert text to speech
            tts = gTTS(text=news_text, lang=lang)
            tts.save("news_audio.mp3")

            # Save uploaded face image
            with open("input_face.jpg", "wb") as f:
                f.write(face_img.read())

            # Ensure results directory exists
            if not os.path.exists("results"):
                os.makedirs("results")

            # Run Wav2Lip
            command = (
                f"python Wav2Lip/inference.py "
                f"--checkpoint_path {checkpoint_path} "
                f"--face input_face.jpg "
                f"--audio news_audio.mp3"
            )
            st.info(f"🌀 Running Wav2Lip with command:\n`{command}`")
            exit_code = os.system(command)

            video_path = "results/result_voice.mp4"
            if exit_code == 0 and os.path.exists(video_path):
                st.success("✅ Video generated successfully!")
                st.video(video_path)
                with open(video_path, "rb") as f:
                    st.download_button("⬇️ Download Video", f, file_name="AI_News.mp4", mime="video/mp4")
            else:
                st.error("❌ Video generation failed. Check if the Wav2Lip model ran properly.")

        except Exception as e:
            st.error(f"❌ Error occurred: {str(e)}")
    else:
        st.warning("⚠️ Please enter the news and upload an image.")
