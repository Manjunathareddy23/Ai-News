import streamlit as st
from langdetect import detect
from gtts import gTTS
import os
from moviepy.editor import *

st.set_page_config(page_title="AI News Reader", layout="centered")
st.title("🗞️ AI News Reader (Free Version)")

# 1. Input news content
news_text = st.text_area("📜 Paste your news content here")

# 2. Upload face image
face_img = st.file_uploader("🖼️ Upload a face image (JPG/PNG)", type=["jpg", "png"])

# 3. Generate Button
if st.button("🎬 Generate Video"):
    if news_text and face_img:
        st.success("✅ Processing started...")

        try:
            # Detect language
            lang = detect(news_text)
            st.info(f"🌐 Detected Language: `{lang}`")

            # Convert text to speech
            tts = gTTS(text=news_text, lang=lang)
            tts.save("news_audio.mp3")

            # Save uploaded image
            with open("input_face.jpg", "wb") as f:
                f.write(face_img.read())

            # Run Wav2Lip (make sure the model is downloaded)
            st.info("🌀 Generating lip-sync video using Wav2Lip...")
            os.system("python Wav2Lip/inference.py --checkpoint_path Wav2Lip/checkpoints/wav2lip_gan.pth --face input_face.jpg --audio news_audio.mp3")

            # Display and allow video download
            video_path = "results/result_voice.mp4"
            if os.path.exists(video_path):
                st.video(video_path)
                with open(video_path, "rb") as f:
                    st.download_button("⬇️ Download Video", f, file_name="AI_News.mp4", mime="video/mp4")
            else:
                st.error("❌ Video generation failed. Please check Wav2Lip execution.")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    else:
        st.warning("⚠️ Please enter news content and upload a face image.")
