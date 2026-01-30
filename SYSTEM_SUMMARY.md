# 🎙️ RepoRadio Debug Logging System - Complete Implementation

## ✅ What's Been Done

### 1. **Debug Logging Module** (`src/debug_logger.py`)
- ✅ Centralized logging configuration
- ✅ Per-module loggers (brain, voice, ingest, app)
- ✅ Automatic log file creation with timestamps
- ✅ Helper functions for each service
- ✅ Dual output: Console (INFO+) and Files (DEBUG+)

### 2. **Integration Across All Modules**
- ✅ **src/brain.py**: Ollama API requests/responses with timing
- ✅ **src/voice.py**: TTS rendering with character voices and durations
- ✅ **src/ingest.py**: Daytona sandbox and git operations
- ✅ **src/app.py**: Pipeline events and user interactions

### 3. **Logging Outputs**
```
logs/
├── app_YYYYMMDD_HHMMSS.log        # UI & pipeline events
├── brain_YYYYMMDD_HHMMSS.log      # AI model interactions
├── ingest_YYYYMMDD_HHMMSS.log     # Repository analysis
└── voice_YYYYMMDD_HHMMSS.log      # Audio synthesis
```

### 4. **Documentation**
- ✅ [DEBUG_LOGGING.md](DEBUG_LOGGING.md) - Comprehensive usage guide
- ✅ [LOGGING_IMPLEMENTATION.md](LOGGING_IMPLEMENTATION.md) - Implementation summary

## 🎯 What Gets Logged

### Brain Module (Ollama/AI)
```
🔌 Ollama Request: model=llama3.1:8b, url=http://...
   Prompt preview: You are the producer...
✅ Ollama Response (456 chars)
   Preview: [{"speaker": "Alex", "text": "..."}]
   Duration: 25000.45ms
```

### Voice Module (Audio)
```
🎙️ Kokoro rendered Alex: 44100 samples @ 24000Hz
🔊 ElevenLabs Request: voice_id=JBFqnCBsd6RMkjVDRZzb
✅ ElevenLabs Response: saved to temp_0.wav
   File size: 125450 bytes
```

### Ingest Module (Repo)
```
🚀 Sandbox created: abc123def456
📦 Successfully cloned https://github.com/...
📖 README size: 2450 chars
📁 File tree size: 1890 chars
💥 Sandbox deleted: abc123def456
```

### App Module (Pipeline)
```
📻 Generate button clicked
📻 Stage 1: Ingesting repository
📻 Stage 2: Generating script
🎙️ Script generated for hosts: Alex, Sam
📻 Stage 3: Rendering audio
📻 Pipeline complete
```

## 🚀 Usage

No changes needed! Logging works automatically:

```bash
# Run the app normally
OLLAMA_HOST=192.168.1.119 streamlit run src/app.py

# Logs appear in logs/ directory automatically
# Check them for debugging:
grep "Ollama Error" logs/brain_*.log
grep "ElevenLabs" logs/voice_*.log
tail -f logs/app_*.log
```

## 📊 Project Structure

```
hacka/
├── src/
│   ├── app.py                    # Streamlit UI (integrated logging)
│   ├── brain.py                  # AI script generation (logging Ollama)
│   ├── voice.py                  # Audio rendering (logging TTS)
│   ├── ingest.py                 # Repo analysis (logging Daytona)
│   ├── debug_logger.py          # ⭐ NEW: Central logging module
│   └── characters/               # Character personalities
│       ├── alex.json
│       ├── sam.json
│       └── marcus.json
├── logs/                         # Auto-generated log files
├── DEBUG_LOGGING.md              # Complete logging guide
├── LOGGING_IMPLEMENTATION.md     # Implementation details
└── requirements.txt              # Dependencies

```

## 📈 Performance Metrics

All logs include:
- ✅ **Timestamps** (YYYY-MM-DD HH:MM:SS)
- ✅ **Module name** (brain, voice, ingest, app)
- ✅ **Log level** (DEBUG, INFO, WARNING, ERROR)
- ✅ **Duration/timing** (for API calls and rendering)
- ✅ **Full error context** (exceptions with context)
- ✅ **Service details** (voice IDs, model names, URLs)

## 🔍 Troubleshooting with Logs

### Find Ollama issues
```bash
grep "Ollama Error" logs/brain_*.log
grep "timeout" logs/brain_*.log
```

### Find voice errors
```bash
grep "Error rendering" logs/voice_*.log
grep "skip" logs/voice_*.log
```

### Find repo issues
```bash
grep "Git clone failed" logs/ingest_*.log
grep "Sandbox" logs/ingest_*.log
```

### Real-time monitoring
```bash
tail -f logs/app_*.log
```

## ✨ Key Features

1. **Non-Intrusive**: Console output stays clean (INFO level)
2. **Comprehensive**: All DEBUG info goes to files
3. **Per-Module**: Separate logs for each service
4. **Timestamped**: Files include timestamp in name
5. **Helper Functions**: Easy logging throughout code
6. **Error Tracking**: Full context for all errors
7. **Performance Data**: Timing for all API calls
8. **Graceful Failures**: Logs individual line failures in voice.py

## 📝 Latest Commit

```
f4f3064 Add comprehensive debug logging system for all modules

- Created src/debug_logger.py with centralized logging
- Logs Ollama API requests/responses with timing
- Logs ElevenLabs and Kokoro TTS operations
- Logs Daytona sandbox lifecycle and git operations
- Logs app pipeline stages and user interactions
- Separate log files per module with timestamps
- Added comprehensive usage documentation
- Updated .gitignore to exclude logs/
```

## 🎁 Ready to Use

Everything is configured and ready to go:
- ✅ No manual setup needed
- ✅ Logs created automatically on first run
- ✅ All modules integrated
- ✅ Fully tested
- ✅ Documented
- ✅ Committed to git

Happy debugging! 🚀
