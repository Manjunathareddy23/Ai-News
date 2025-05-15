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
            # Detect language
            lang = detect(news_text)
            st.info(f"🌐 Detected Language: `{lang}`")

            # Convert text to audio using gTTS
            tts = gTTS(text=news_text, lang=lang)
            tts.save("news_audio.mp3")

            # Save uploaded face image to file
            with open("input_face.jpg", "wb") as f:
                f.write(face_img.read())

            st.info("🌀 Running Wav2Lip...")
            exit_code = os.system(
                "python Wav2Lip/inference.py --checkpoint_path Wav2Lip/checkpoints/wav2lip_gan.pth "
                "--face input_face.jpg --audio news_audio.mp3"
            )

            video_path = "results/result_voice.mp4"
            if exit_code == 0 and os.path.exists(video_path):
                st.video(video_path)
                with open(video_path, "rb") as f:
                    st.download_button("⬇️ Download Video", f, file_name="AI_News.mp4", mime="video/mp4")
            else:
                st.error("❌ Video generation failed. Check if Wav2Lip ran correctly and the model file exists.")

        except Exception as e:
            st.error(f"❌ Error occurred: {str(e)}")
    else:
        st.warning("⚠️ Please enter news and upload an image.")
