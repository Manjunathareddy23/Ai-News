import streamlit as st
from langdetect import detect
from gtts import gTTS
import os
from moviepy.editor import *

st.title("🗞️ AI News Reader (Free Version)")

# 1. Text Input
news_text = st.text_area("Paste your news content here")

# 2. Face Image Upload
face_img = st.file_uploader("Upload a face image (jpg/png)", type=["jpg", "png"])

# 3. Generate and Process
if st.button("Generate Video"):
    if news_text and face_img:
        st.success("Processing...")

        # Detect language
        lang = detect(news_text)
        st.write(f"Detected Language: {lang}")

        # Text-to-Speech
        tts = gTTS(text=news_text, lang=lang)
        tts.save("news_audio.mp3")

        # Save image
        with open("input_face.jpg", "wb") as f:
            f.write(face_img.read())

        st.info("Generating lip-sync video using Wav2Lip...")

        os.system("python Wav2Lip/inference.py --checkpoint_path Wav2Lip/checkpoints/wav2lip_gan.pth --face input_face.jpg --audio news_audio.mp3")

        # Show video
        video_path = "results/result_voice.mp4"
        st.video(video_path)
        with open(video_path, "rb") as file:
            st.download_button("Download Video", file, file_name="AI_News.mp4")

    else:
        st.error("Please provide both news text and a face image.")
