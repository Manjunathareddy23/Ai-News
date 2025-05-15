import streamlit as st
from langdetect import detect
from gtts import gTTS
import os

st.set_page_config(page_title="AI News Reader", layout="centered")
st.title("🗞️ AI News Reader (Free Version)")

news_text = st.text_area("📜 Paste your news content here")

face_img = st.file_uploader("🖼️ Upload a face image (JPG/PNG)", type=["jpg", "png"])

if st.button("🎬 Generate Video"):
    if news_text and face_img:
        st.success("✅ Processing started...")

        try:
            lang = detect(news_text)
            st.info(f"🌐 Detected Language: `{lang}`")

            tts = gTTS(text=news_text, lang=lang)
            tts.save("news_audio.mp3")

            with open("input_face.jpg", "wb") as f:
                f.write(face_img.read())

            # Ensure results folder exists
            if not os.path.exists("results"):
                os.makedirs("results")

            # Check where your checkpoint actually is:
            checkpoint_path = "Wav2Lip/checkpoints/wav2lip_gan.pth"
            if not os.path.isfile(checkpoint_path):
                # If not there, check root (your current location)
                if os.path.isfile("wav2lip_gan.pth"):
                    checkpoint_path = "wav2lip_gan.pth"
                else:
                    st.error("❌ Checkpoint file not found! Please upload 'wav2lip_gan.pth' in 'Wav2Lip/checkpoints/' or root folder.")
                    st.stop()

            command = f"python Wav2Lip/inference.py --checkpoint_path {checkpoint_path} --face input_face.jpg --audio news_audio.mp3"
            st.info(f"🌀 Running Wav2Lip with command:\n`{command}`")

            exit_code = os.system(command)

            video_path = "results/result_voice.mp4"
            if exit_code == 0 and os.path.exists(video_path):
                st.video(video_path)
                with open(video_path, "rb") as f:
                    st.download_button("⬇️ Download Video", f, file_name="AI_News.mp4", mime="video/mp4")
            else:
                st.error("❌ Video generation failed. Check logs for errors and confirm model checkpoint exists.")

        except Exception as e:
            st.error(f"❌ Error occurred: {str(e)}")
    else:
        st.warning("⚠️ Please enter news and upload an image.")
