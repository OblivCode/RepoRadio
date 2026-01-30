import streamlit as st
import glob
import os
from ingest import get_repo_content
from brain import generate_script
# IMPORTS THE SMART VOICE ENGINE (Triggers auto-download)
from voice import render_audio 
from debug_logger import app_logger, log_app_event, log_script_generation 

st.set_page_config(page_title="RepoRadio", page_icon="📻")
st.title("📻 RepoRadio")

# --- 1. SCAN FOR CHARACTERS ---
# Look for json files in the characters folder
character_files = glob.glob("characters/*.json")
character_names = [os.path.basename(f).replace(".json", "").capitalize() for f in character_files]

if not character_names:
    st.error("⚠️ No character files found in /characters! Please add some JSON files.")
    st.stop()

# --- 2. THE UI ---
repo_url = st.text_input("Paste GitHub URL", "https://github.com/daytonaio/daytona")

col1, col2 = st.columns(2)
with col1:
    host1 = st.selectbox("🎙️ Host 1", character_names, index=0)
with col2:
    default_idx = 1 if len(character_names) > 1 else 0
    host2 = st.selectbox("🎙️ Host 2", character_names, index=default_idx)

# Advanced settings
with st.expander("⚙️ Settings"):
    c1, c2 = st.columns(2)
    provider = c1.selectbox("AI Brain", ["Local (Ollama)", "Cloud (Siray/OpenAI)"])
    voice_provider = c2.selectbox("Voice Engine", ["Local (Kokoro)", "Cloud (ElevenLabs)"])
    # Deep mode toggle
    deep_mode = st.checkbox("🕵️ Enable Deep Radio (Agentic Read)", value=True)

# --- 3. GENERATE BUTTON ---
if st.button("GENERATE VIBE"):
    if not repo_url:
        st.error("Bro, drop a link first.")
    else:
        log_app_event("Generate button clicked", f"URL: {repo_url}, Hosts: {host1} & {host2}")
        status = st.empty()
        
        # 1. Ingest
        status.info(f"🚀 Spinning up Daytona Sandbox...")
        log_app_event("Stage 1: Ingesting repository", repo_url)
        content = get_repo_content(repo_url, deep_mode=deep_mode, provider=provider)
        
        with st.expander("See Raw Content"):
            st.text_area("Debug", content, height=300)
        
        # 2. Brain
        status.info(f"🎙️ Writing script for {host1} & {host2}...")
        log_app_event("Stage 2: Generating script", f"Provider: {provider}")
        script = generate_script(content, host1, host2, provider)
        log_script_generation([host1, host2], len(str(script)))
        st.json(script)
        
        # 3. Voice
        status.info(f"🔊 Synthesizing audio...")
        log_app_event("Stage 3: Rendering audio", f"Provider: {voice_provider}")
        # This now calls the function in voice.py, which ensures models exist
        audio_file = render_audio(script, voice_provider)
        
        log_app_event("Pipeline complete", f"Output: {audio_file}")
        status.success("✅ Episode Ready!")
        st.audio(audio_file)