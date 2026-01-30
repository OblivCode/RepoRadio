"""
Debug logging module for RepoRadio.
Logs outputs from all services: Ollama, ElevenLabs, Daytona, etc.
"""
import os
import logging
from datetime import datetime
from pathlib import Path

# Create logs directory
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Timestamp for log files
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Configure loggers for each module
def setup_logger(module_name: str, level=logging.DEBUG) -> logging.Logger:
    """
    Setup a logger for a specific module with both file and console handlers.
    
    Args:
        module_name: Name of the module (e.g., 'brain', 'voice', 'ingest', 'app')
        level: Logging level (default: DEBUG)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(module_name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.hasHandlers():
        return logger
    
    # File handler - one per module
    log_file = LOGS_DIR / f"{module_name}_{TIMESTAMP}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# Module-specific loggers
brain_logger = setup_logger("brain")
voice_logger = setup_logger("voice")
ingest_logger = setup_logger("ingest")
app_logger = setup_logger("app")


def log_ollama_request(model: str, prompt_preview: str, url: str):
    """Log Ollama API request."""
    brain_logger.debug(f"🔌 Ollama Request: model={model}, url={url}")
    brain_logger.debug(f"   Prompt preview: {prompt_preview[:100]}...")


def log_ollama_response(response_text: str, duration_ms: float = None):
    """Log Ollama API response."""
    brain_logger.debug(f"✅ Ollama Response ({len(response_text)} chars)")
    brain_logger.debug(f"   Preview: {response_text[:100]}...")
    if duration_ms:
        brain_logger.debug(f"   Duration: {duration_ms:.2f}ms")


def log_ollama_error(error: str, url: str = None):
    """Log Ollama errors."""
    brain_logger.error(f"❌ Ollama Error: {error}")
    if url:
        brain_logger.debug(f"   URL: {url}")


def log_elevenlabs_request(text: str, voice_id: str):
    """Log ElevenLabs API request."""
    voice_logger.debug(f"🔊 ElevenLabs Request: voice_id={voice_id}")
    voice_logger.debug(f"   Text preview: {text[:100]}...")


def log_elevenlabs_response(audio_file: str, file_size: int = None):
    """Log ElevenLabs API response."""
    voice_logger.debug(f"✅ ElevenLabs Response: saved to {audio_file}")
    if file_size:
        voice_logger.debug(f"   File size: {file_size} bytes")


def log_elevenlabs_error(error: str):
    """Log ElevenLabs errors."""
    voice_logger.error(f"❌ ElevenLabs Error: {error}")


def log_daytona_sandbox(action: str, sandbox_id: str = None):
    """Log Daytona sandbox operations."""
    ingest_logger.debug(f"🚀 Daytona: {action}")
    if sandbox_id:
        ingest_logger.debug(f"   Sandbox ID: {sandbox_id}")


def log_daytona_error(error: str):
    """Log Daytona errors."""
    ingest_logger.error(f"❌ Daytona Error: {error}")


def log_git_clone(repo_url: str, success: bool, error: str = None):
    """Log git clone operations."""
    if success:
        ingest_logger.debug(f"📦 Git clone succeeded: {repo_url}")
    else:
        ingest_logger.error(f"❌ Git clone failed: {repo_url}")
        if error:
            ingest_logger.debug(f"   Error: {error}")


def log_character_load(char_name: str, success: bool, error: str = None):
    """Log character loading."""
    if success:
        brain_logger.debug(f"👤 Character loaded: {char_name}")
    else:
        brain_logger.warning(f"⚠️ Character load failed: {char_name}")
        if error:
            brain_logger.debug(f"   Error: {error}")


def log_script_generation(hosts: list, script_length: int):
    """Log script generation."""
    app_logger.debug(f"🎙️ Script generated for hosts: {', '.join(hosts)}")
    app_logger.debug(f"   Script length: {script_length} chars")


def log_audio_rendering(speaker: str, audio_file: str, duration_ms: float = None):
    """Log audio rendering."""
    voice_logger.debug(f"🎙️ Rendered: {speaker} → {audio_file}")
    if duration_ms:
        voice_logger.debug(f"   Duration: {duration_ms:.2f}ms")


def log_app_event(event: str, details: str = None):
    """Log general app events."""
    app_logger.info(f"📻 {event}")
    if details:
        app_logger.debug(f"   {details}")
