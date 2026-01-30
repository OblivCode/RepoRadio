# Debug Logging Implementation Summary

## What Was Added

A comprehensive debug logging system for RepoRadio that captures all service outputs and API interactions.

## Key Components

### 1. **src/debug_logger.py** (New)
- Centralized logging module with per-module loggers
- Automatic log file creation in `logs/` directory with timestamps
- Helper functions for logging specific events from each service:
  - `log_ollama_request()` - AI model API calls
  - `log_ollama_response()` - AI model outputs
  - `log_elevenlabs_request()` - Cloud TTS API calls
  - `log_elevenlabs_response()` - TTS API responses
  - `log_daytona_sandbox()` - Repository sandbox operations
  - `log_git_clone()` - Git operations
  - `log_character_load()` - Character personality file loading
  - `log_audio_rendering()` - Audio synthesis progress
  - `log_app_event()` - Pipeline stage transitions

### 2. **Updated Modules**
All four core modules now integrated with logging:

- **src/brain.py**
  - Logs Ollama requests with model name and prompt preview
  - Logs full API responses with duration
  - Logs character loading success/failure
  - Logs JSON parsing errors with context
  - Logs timeout errors

- **src/voice.py**
  - Logs script format validation
  - Logs per-line rendering with speaker names
  - Logs Kokoro parameters (samples, sample rate)
  - Logs ElevenLabs API calls and file sizes
  - Logs individual line failures (graceful degradation)

- **src/ingest.py**
  - Logs Daytona sandbox creation/deletion with IDs
  - Logs git clone operations (success/failure)
  - Logs file extraction (README and file tree sizes)
  - Logs cleanup operations

- **src/app.py**
  - Logs button clicks with parameters
  - Logs pipeline stage transitions
  - Logs character selections
  - Logs final output file

### 3. **Documentation**
- **DEBUG_LOGGING.md** - Comprehensive guide with:
  - What gets logged and where
  - How to read and interpret logs
  - Example log entries
  - Troubleshooting commands
  - API reference for logging functions
  - Cleanup procedures

### 4. **Updated .gitignore**
- Excludes `logs/` directory (auto-generated)
- Excludes temporary audio files
- Excludes test artifacts
- Excludes large model files

## Log File Structure

```
logs/
├── app_YYYYMMDD_HHMMSS.log        # Pipeline and UI events
├── brain_YYYYMMDD_HHMMSS.log      # AI model interactions
├── ingest_YYYYMMDD_HHMMSS.log     # Repository analysis
└── voice_YYYYMMDD_HHMMSS.log      # Audio synthesis
```

Each file contains:
- Timestamp (YYYY-MM-DD HH:MM:SS)
- Logger name (module)
- Log level (DEBUG, INFO, WARNING, ERROR)
- Message with relevant context

## Usage

No changes needed to use the app! Logging happens automatically:

```bash
# Run the app normally
OLLAMA_HOST=192.168.1.119 streamlit run src/app.py

# Logs are automatically created in logs/ directory
# Check logs for debugging:
grep "Ollama Error" logs/brain_*.log
grep "Error rendering" logs/voice_*.log
tail -f logs/app_*.log  # Real-time app events
```

## Benefits

1. **Full Observability**: See exactly what every service is doing
2. **Easy Debugging**: Find issues with grep commands (see DEBUG_LOGGING.md)
3. **Performance Metrics**: Ollama response times and audio rendering durations logged
4. **Audit Trail**: Complete record of all API interactions
5. **Error Context**: Full error messages with surrounding context
6. **Non-Intrusive**: Console stays clean (INFO level), files have all DEBUG details

## Testing

All loggers tested and working:
- ✅ brain_logger: Ollama API logging
- ✅ voice_logger: Audio synthesis logging  
- ✅ ingest_logger: Repository ingestion logging
- ✅ app_logger: Pipeline events logging
- ✅ Log files created with timestamps
- ✅ No breaking changes to existing functionality

## Git Status

Commit: `Add comprehensive debug logging system for all modules`
- 7 files changed
- 527 insertions (+)
- 5 deletions (-)

Ready to push!
