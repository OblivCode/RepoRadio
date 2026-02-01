import streamlit as st
import glob
import os
import json
from ingest import get_repo_content
from brain import generate_script
# IMPORTS THE SMART VOICE ENGINE (Triggers auto-download)
from voice import render_audio 
from debug_logger import app_logger, log_app_event, log_script_generation 

st.set_page_config(page_title="RepoRadio", page_icon="📻", layout="wide")
st.title("📻 RepoRadio")

# --- 1. LOAD CHARACTER DATA ---
# Load full character data including descriptions
def load_all_characters():
    """Load all character JSON files with full metadata."""
    character_files = glob.glob("src/characters/*.json")
    characters = {}
    for filepath in character_files:
        name = os.path.basename(filepath).replace(".json", "").capitalize()
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                characters[name] = data
        except Exception as e:
            st.warning(f"Failed to load {name}: {e}")
    return characters

characters_data = load_all_characters()

if not characters_data:
    st.error("⚠️ No character files found in /characters! Please add some JSON files.")
    st.stop()

# --- 2. THE UI ---
repo_url = st.text_input("📎 Paste GitHub URL", "https://github.com/daytonaio/daytona")

st.markdown("---")
st.subheader("🎙️ Select Your Hosts")

# Host selection with variable count (1-3)
num_hosts = st.radio("Number of Hosts:", [1, 2, 3], index=1, horizontal=True)

# Character card selection
hosts = []
character_names = list(characters_data.keys())

# Create emoji mapping for personality types
personality_emojis = {
    "hype": "🚀",
    "cynical": "😒", 
    "paranoid": "🔒",
    "pragmatic": "📊",
    "devops": "⚙️",
    "junior": "🌟",
    "purist": "🐧"
}

def get_character_emoji(description):
    """Get emoji based on character personality."""
    desc_lower = description.lower()
    if "hype" in desc_lower: return "🚀"
    if "cynical" in desc_lower or "tired" in desc_lower: return "😒"
    if "paranoid" in desc_lower or "security" in desc_lower: return "🔒"
    if "pragmatic" in desc_lower or "pm" in desc_lower: return "📊"
    if "devops" in desc_lower or "infrastructure" in desc_lower: return "⚙️"
    if "junior" in desc_lower or "optimistic" in desc_lower: return "🌟"
    if "purist" in desc_lower or "open source" in desc_lower: return "🐧"
    return "🎤"

cols = st.columns(num_hosts)
for i in range(num_hosts):
    with cols[i]:
        st.markdown(f"### Host {i+1}")
        
        # Radio buttons for character selection with descriptions
        selected = st.radio(
            f"Choose Host {i+1}:",
            options=character_names,
            index=min(i, len(character_names) - 1),
            key=f"host_{i}",
            label_visibility="collapsed"
        )
        
        # Display character card
        char_data = characters_data[selected]
        emoji = get_character_emoji(char_data.get("description", ""))
        
        st.markdown(f"""
        <div style="
            border: 2px solid #4CAF50;
            border-radius: 10px;
            padding: 15px;
            background-color: #f0f8ff;
            margin-top: 10px;
        ">
            <h4 style="margin: 0; color: #2c3e50;">{emoji} {char_data['name']}</h4>
            <p style="margin: 10px 0 0 0; color: #555; font-size: 14px;">
                {char_data.get('description', 'No description available')}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        hosts.append(selected)

# Optional: Warn about duplicate selections
if len(hosts) != len(set(hosts)):
    st.warning("⚠️ You selected the same character multiple times!")

st.markdown("---")

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
        log_app_event("Generate button clicked", f"URL: {repo_url}, Hosts: {', '.join(hosts)}")
        status = st.empty()
        
        # 1. Ingest
        status.info(f"🚀 Spinning up Daytona Sandbox...")
        log_app_event("Stage 1: Ingesting repository", repo_url)
        content = get_repo_content(repo_url, deep_mode=deep_mode, provider=provider)
        
        with st.expander("See Raw Content"):
            st.text_area("Debug", content, height=300)
        
        # 2. Brain
        status.info(f"🎙️ Writing script for {', '.join(hosts)}...")
        log_app_event("Stage 2: Generating script", f"Hosts: {', '.join(hosts)}, Provider: {provider}")
        script = generate_script(content, hosts, provider)
        log_script_generation(hosts, len(str(script)))
        st.json(script)
        
        # 3. Voice
        status.info(f"🔊 Synthesizing audio...")
        log_app_event("Stage 3: Rendering audio", f"Provider: {voice_provider}")
        # This now calls the function in voice.py, which ensures models exist
        audio_file = render_audio(script, voice_provider)
        
        log_app_event("Pipeline complete", f"Output: {audio_file}")
        status.success("✅ Episode Ready!")
        st.audio(audio_file)