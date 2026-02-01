# 📻 RepoRadio

**AI-Generated Podcast Reviews of GitHub Repositories**

Turn any GitHub repository into an entertaining, educational podcast with multiple host personalities, background music, sponsor breaks, and professional audio production.

---

## 🎯 What is RepoRadio?

RepoRadio analyzes GitHub repositories and generates natural-sounding podcast conversations between tech experts discussing the code, architecture, dependencies, and interesting technical details. Think "tech podcast meets code review."

### Key Features

🎙️ **8 Unique Host Personalities**
- Alex (Hype Developer), Casey (Tech Enthusiast), Jordan (Pragmatic PM)
- Morgan (Cynical Senior), Quinn (Security Paranoid), Riley (Junior Optimistic)
- Sam (DevOps Wizard), Taylor (Open Source Purist)

🎬 **Production Studio Features** (All enabled by default)
- 🎵 Background lo-fi music with auto-ducking
- 🎺 Intro/outro jingles
- 📢 Humorous sponsor ads based on project dependencies
- 🎚️ Crossfade transitions between speakers
- 🔊 Professional audio mixing

🤖 **Intelligent Analysis**
- Git archaeology (recent commits, top contributors)
- Dependency scanning (package.json, requirements.txt, etc.)
- Deep mode: AI-selected priority files for code review
- Daytona sandbox for safe repo cloning

🔊 **Voice Options**
- Local: Kokoro ONNX (fast, private, free)
- Cloud: ElevenLabs (premium quality)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.ai) with llama3.1:8b model
- [Daytona](https://daytona.io) for sandboxed repo access

### Installation

1. Clone and install
\`\`\`bash
git clone <your-repo-url>
cd hacka
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
\`\`\`

2. Set up Ollama
\`\`\`bash
ollama pull llama3.1:8b
\`\`\`

3. Configure environment
\`\`\`bash
cp .env.example .env
# Edit .env and set your DAYTONA_API_KEY
\`\`\`

4. Run
\`\`\`bash
./start.sh  # or: streamlit run src/app.py
\`\`\`

---

## 🎮 Usage

1. Open http://localhost:8501
2. Paste a GitHub URL
3. Select 1-3 hosts from 8 personalities
4. Click GENERATE VIBE
5. Listen to your podcast! 🎧

---

## 🏗️ Architecture

### Script Generation (One-Line-at-a-Time)
- Generate ONE line at a time (8-12 iterations)
- Pre-break: 4-6 lines introducing the project
- Ad break: 1 sponsor announcement (if enabled)
- Post-break: 4-6 lines diving into technical details
- 100% reliable - no more truncation issues

### Audio Production Pipeline
1. Parallel TTS (4 workers, ~10s for 12 lines)
2. Crossfade transitions (200ms)
3. Sponsor ad transition sounds
4. Background music overlay (-20dB)
5. Intro/outro jingles
6. Export to MP3

---

## 🧪 Testing

\`\`\`bash
PYTHONPATH=src:\$PYTHONPATH pytest tests/ -v
\`\`\`

All 15 unit tests passing ✅

---

## 📝 Documentation

- **PRODUCTION_STUDIO.md**: Audio features guide
- **DEBUG_LOGGING.md**: Logging system
- **src/music/README.md**: Music folder organization

---

## 🛣️ Roadmap

- [ ] Cloud LLM support (OpenAI/Anthropic)
- [ ] Export to YouTube/SoundCloud
- [ ] Multi-language support
- [ ] Voice cloning for custom characters

---

## 🤝 Contributing

Contributions welcome! Areas: characters, ad templates, music, tests, performance.

---

## 📄 License

MIT License

---

## 🙏 Credits

- **Kokoro TTS**: hexgrad/Kokoro-82M
- **Daytona**: Sandboxed dev environments
- **Ollama**: Local LLM inference
- **Streamlit**: Web UI

---

*RepoRadio: Where code meets conversation* 🎙️✨
