# 📻 RepoRadio - Debug Logging System

## Overview

RepoRadio now includes a comprehensive debug logging system that captures outputs from all services and modules, making it easy to troubleshoot and understand what's happening behind the scenes.

## Log Files

Debug logs are automatically created in the `logs/` directory with timestamps for each module:

```
logs/
├── brain_YYYYMMDD_HHMMSS.log      # AI model requests/responses, script generation
├── voice_YYYYMMDD_HHMMSS.log      # Audio rendering (Kokoro & ElevenLabs)
├── ingest_YYYYMMDD_HHMMSS.log     # Repository ingestion (Daytona sandbox)
└── app_YYYYMMDD_HHMMSS.log        # Overall pipeline and UI events
```

## What Gets Logged

### Brain Module (`src/brain.py`)
- **Ollama API Requests**: Model name, endpoint URL, prompt preview
- **Ollama API Responses**: Response text (full), duration in milliseconds
- **Ollama Errors**: Connection errors, timeouts, JSON parsing issues
- **Character Loading**: Success/failure when loading personality JSON files
- **Script Generation**: Input validation, response format checks

**Example Log Entry:**
```
2024-01-30 12:51:45 - brain - DEBUG - 🔌 Ollama Request: model=llama3.1:8b, url=http://192.168.1.119:11434/api/generate
2024-01-30 12:51:45 - brain - DEBUG -    Prompt preview: You are the producer of 'RepoRadio'...
2024-01-30 12:52:10 - brain - DEBUG - ✅ Ollama Response (456 chars)
2024-01-30 12:52:10 - brain - DEBUG -    Preview: [{"speaker": "Alex", "text": "..."}]
2024-01-30 12:52:10 - brain - DEBUG -    Duration: 25000.45ms
```

### Voice Module (`src/voice.py`)
- **Kokoro TTS**: Character voice selection, sample rate, rendering duration
- **ElevenLabs API**: Text requests, voice IDs, file sizes, API responses
- **Audio Rendering**: Speaker names, text previews, output files, durations
- **Error Handling**: Per-line errors (skipped lines are logged)

**Example Log Entry:**
```
2024-01-30 12:52:11 - voice - INFO - Starting audio render with Local (Kokoro)
2024-01-30 12:52:11 - voice - DEBUG - Script contains 3 lines
2024-01-30 12:52:11 - voice - DEBUG - Line 0 - Alex (voice_id=am_michael): This repository is a game-changing tool for developers...
2024-01-30 12:52:12 - voice - DEBUG - Kokoro rendered Alex: 44100 samples @ 24000Hz
2024-01-30 12:52:12 - voice - DEBUG - 🎙️ Rendered: Alex → temp_0.wav
2024-01-30 12:52:12 - voice - DEBUG -    Duration: 1250.33ms
```

### Ingest Module (`src/ingest.py`)
- **Daytona Sandbox**: Creation, deletion, sandbox IDs
- **Git Clone Operations**: Repository URL, success/failure, error messages
- **File Extraction**: README size, file tree size
- **Sandbox Lifecycle**: All state transitions

**Example Log Entry:**
```
2024-01-30 12:51:30 - ingest - INFO - Starting repo analysis: https://github.com/daytonaio/daytona
2024-01-30 12:51:30 - ingest - DEBUG - Sandbox created: abc123def456
2024-01-30 12:51:30 - ingest - DEBUG - Repository name: daytona
2024-01-30 12:51:35 - ingest - INFO - Successfully cloned https://github.com/daytonaio/daytona
2024-01-30 12:51:36 - ingest - DEBUG - README size: 2450 chars
2024-01-30 12:51:36 - ingest - DEBUG - File tree size: 1890 chars
2024-01-30 12:51:37 - ingest - INFO - Repo analysis complete: 4340 chars total
```

### App Module (`src/app.py`)
- **Pipeline Events**: Stage transitions (ingest → brain → voice)
- **User Interactions**: Button clicks, host selections, settings changes
- **Script Generation Details**: Character names, output size
- **Completion Status**: Success/failure of entire pipeline

**Example Log Entry:**
```
2024-01-30 12:51:25 - app - INFO - 📻 Generate button clicked
2024-01-30 12:51:25 - app - DEBUG -    URL: https://github.com/daytonaio/daytona, Hosts: Alex & Sam
2024-01-30 12:51:25 - app - INFO - 📻 Stage 1: Ingesting repository
2024-01-30 12:51:25 - app - DEBUG -    https://github.com/daytonaio/daytona
2024-01-30 12:52:10 - app - INFO - 📻 Stage 2: Generating script
2024-01-30 12:52:10 - app - DEBUG -    Provider: Local (Ollama)
2024-01-30 12:52:10 - app - DEBUG - 🎙️ Script generated for hosts: Alex, Sam
2024-01-30 12:52:10 - app - DEBUG -    Script length: 2341 chars
2024-01-30 12:52:12 - app - INFO - 📻 Stage 3: Rendering audio
2024-01-30 12:52:12 - app - DEBUG -    Provider: Local (Kokoro)
2024-01-30 12:52:20 - app - INFO - 📻 Pipeline complete
2024-01-30 12:52:20 - app - DEBUG -    Output: final_episode.mp3
```

## Log Levels

Each log entry has a level that indicates severity:

| Level | Icon | Use Case | Color in Terminal |
|-------|------|----------|-------------------|
| **DEBUG** | 🔍 | Detailed information for troubleshooting | Gray |
| **INFO** | ℹ️ | General informational messages | Blue |
| **WARNING** | ⚠️ | Warning messages (non-fatal issues) | Yellow |
| **ERROR** | ❌ | Error messages (failures) | Red |

## How to Read the Logs

### Find Ollama Issues
```bash
grep "Ollama" logs/brain_*.log
grep "ERROR" logs/brain_*.log
grep "timeout" logs/brain_*.log
```

### Find Voice Generation Issues
```bash
grep "Error rendering" logs/voice_*.log
grep "elevenlabs\|kokoro" logs/voice_*.log -i
```

### Find Repository Analysis Issues
```bash
grep "Git clone failed" logs/ingest_*.log
grep "Sandbox Error" logs/ingest_*.log
```

### Full Pipeline Trace
```bash
# See everything that happened in order across all modules
cat logs/*_YYYYMMDD_HHMMSS.log | sort
```

## Debug Logger API

The debug logging system is located in `src/debug_logger.py` and provides these helper functions:

### Brain Logging
```python
from debug_logger import brain_logger, log_ollama_request, log_ollama_response, log_ollama_error

# Log Ollama request
log_ollama_request(model="llama3.1:8b", prompt_preview="Your prompt...", url="http://...")

# Log successful response
log_ollama_response(response_text="...", duration_ms=1250.5)

# Log error
log_ollama_error("Connection refused", url="http://...")

# Direct logging
brain_logger.debug("Custom debug message")
brain_logger.error("Custom error message")
```

### Voice Logging
```python
from debug_logger import voice_logger, log_elevenlabs_request, log_audio_rendering

# Log ElevenLabs request
log_elevenlabs_request(text="Hello...", voice_id="JBFqnCBsd6RMkjVDRZzb")

# Log audio rendering
log_audio_rendering(speaker="Alex", audio_file="temp_0.wav", duration_ms=1250.5)

# Direct logging
voice_logger.debug("Kokoro rendered successfully")
```

### Ingest Logging
```python
from debug_logger import ingest_logger, log_daytona_sandbox, log_git_clone

# Log sandbox operations
log_daytona_sandbox(action="Creating sandbox", sandbox_id="abc123")

# Log git clone
log_git_clone(repo_url="https://github.com/...", success=True)

# Direct logging
ingest_logger.error("Sandbox creation failed")
```

### App Logging
```python
from debug_logger import app_logger, log_app_event, log_script_generation

# Log application events
log_app_event("Pipeline started", "User clicked GENERATE VIBE")

# Log script generation
log_script_generation(hosts=["Alex", "Sam"], script_length=2341)

# Direct logging
app_logger.info("Application initialized")
```

## Console vs File Logs

- **Console Output**: INFO level and above (important messages)
- **File Output**: DEBUG level and above (everything, for detailed troubleshooting)

This ensures the console stays clean while files capture all details.

## Troubleshooting Guide

### Ollama Connection Issues
1. Check `logs/brain_*.log` for connection errors
2. Look for "Ollama Error" entries
3. Verify OLLAMA_HOST environment variable

### Script Generation Failures
1. Check for JSON parse errors in `logs/brain_*.log`
2. Look for empty response messages
3. Verify model availability in Ollama

### Audio Rendering Problems
1. Check `logs/voice_*.log` for render errors
2. Look for per-line skip messages
3. Verify voice IDs in `src/characters/*.json`

### Sandbox Issues
1. Check `logs/ingest_*.log` for sandbox errors
2. Look for git clone failures
3. Verify Daytona SDK connectivity

## Cleaning Up Old Logs

Logs accumulate over time. To clean up old logs:

```bash
# Keep only logs from today
find logs/ -mtime +7 -delete

# Or remove all logs
rm -rf logs/
```

The logs directory will be recreated automatically on the next run.

## Environment Variables

Logging is controlled by standard Python logging configuration:

- All modules use DEBUG level by default
- To change globally, edit `src/debug_logger.py` and modify the `level` parameter in `setup_logger()`
- Logs are always written to files; console shows INFO and above

## Integration

The logging system is already integrated into:
- ✅ `src/brain.py` - Ollama API calls and script generation
- ✅ `src/voice.py` - Audio rendering and TTS API calls
- ✅ `src/ingest.py` - Daytona sandbox and git operations
- ✅ `src/app.py` - Pipeline events and user interactions

No additional setup is required. Logs are created automatically.
