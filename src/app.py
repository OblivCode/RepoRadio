# Add this to the top of your python files
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os
from ingest import get_repo_content
from brain import generate_script
from voice import render_audio
# We will import the ingest logic later. For now, we mock it to test the UI.
# from ingest import get_repo_content 

st.set_page_config(page_title="RepoRadio", page_icon="📻", layout="centered")

# Custom CSS for the "Vibe" look (Dark Mode + Neon)
st.markdown("""
<style>
    /* Dark Background */
    .stApp {
        background-color: #0E1117;
    }
    /* Neon Inputs */
    .stTextInput > div > div > input {
        background-color: #1E1E1E;
        color: #00FF94;
        border: 1px solid #00FF94;
    }
    /* The "Go" Button */
    .stButton > button {
        width: 100%;
        background-color: #00FF94;
        color: black;
        font-weight: bold;
        border: none;
        padding: 0.5rem;
    }
    .stButton > button:hover {
        background-color: #00CC7A;
        color: black;
        border: 1px solid #fff;
    }
    /* Success Message */
    .stSuccess {
        background-color: #1E1E1E;
        color: #00FF94;
    }
</style>
""", unsafe_allow_html=True)

st.title("📻 RepoRadio")
st.markdown("### Turn GitHub Repos into Podcasts")

# --- Input Section ---
repo_url = st.text_input("Paste GitHub URL", placeholder="https://github.com/daytonaio/daytona")

col1, col2 = st.columns(2)
with col1:
    provider = st.selectbox("AI Brain", ["Local (Ollama)", "Cloud (Siray/OpenAI)"])
with col2:
    voice_provider = st.selectbox("Voice Engine", ["Local (Kokoro)", "Cloud (ElevenLabs)"])

# --- The Logic ---
if st.button("GENERATE VIBE"):
    if not repo_url:
        st.error("Bro, drop a link first.")
    else:
        status = st.empty()
        
        # 1. Ingest
        status.info(f"🚀 Spinning up Daytona Sandbox for {repo_url}...")
        try:
            content = get_repo_content(repo_url)
            with st.expander("See Raw Content", expanded=True):
                st.text_area("Full Scraped Data", content, height=400)
        except Exception as e:
            st.error(f"Ingest failed: {e}")
            st.stop()
        
        # 2. Brain
        status.info("🎙️ Writing script (Alex vs. Sam)...")
        try:
            script = generate_script(content, provider)
            st.json(script) # Show the script to the user
        except Exception as e:
            st.error(f"Script gen failed: {e}")
            st.stop()
        
        # 3. Voice
        status.info(f"🔊 Synthesizing audio with {voice_provider}...")
        try:
            audio_file = render_audio(script, voice_provider)
            status.success("✅ Episode Ready!")
            st.balloons()
            st.audio(audio_file)
        except Exception as e:
            st.error(f"Audio failed: {e}")
            if "Kokoro" in str(e):
                st.warning("Did you download the kokoro-v0_19.onnx file?")