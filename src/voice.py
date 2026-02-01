import os
import requests
import soundfile as sf
import time
from kokoro_onnx import Kokoro
from elevenlabs import ElevenLabs, save
from pydub import AudioSegment
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from debug_logger import voice_logger, log_elevenlabs_request, log_elevenlabs_response, log_elevenlabs_error, log_audio_rendering

# URLs for the models
MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
MODEL_FILE = "kokoro-v1.0.onnx"
VOICES_FILE = "voices-v1.0.bin"

def download_file(url, filename):
    print(f"⬇️  Downloading {filename}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✅ Downloaded {filename}")
    except Exception as e:
        print(f"❌ Failed to download {filename}: {e}")
        # Delete partial file so we try again next time
        if os.path.exists(filename):
            os.remove(filename)

def check_and_install_models():
    """Checks if models exist and are valid (not empty)."""
    
    # Check Model File
    if not os.path.exists(MODEL_FILE) or os.path.getsize(MODEL_FILE) == 0:
        print(f"⚠️  {MODEL_FILE} missing or empty. Downloading...")
        download_file(MODEL_URL, MODEL_FILE)

    # Check Voices File
    if not os.path.exists(VOICES_FILE) or os.path.getsize(VOICES_FILE) == 0:
        print(f"⚠️  {VOICES_FILE} missing or empty. Downloading...")
        download_file(VOICES_URL, VOICES_FILE)

# Run check immediately
check_and_install_models()

# Initialize Kokoro
try:
    print("🔌 Loading Kokoro Model...")
    kokoro = Kokoro(MODEL_FILE, VOICES_FILE)
    print("✅ Local Kokoro TTS Ready.")
except Exception as e:
    print(f"❌ Critical Error loading Kokoro: {e}")
    kokoro = None

# ... [Keep your existing helper functions below] ...

def get_voice_id(character_name, provider):
    try:
        clean_name = character_name.split(" ")[0].lower()
        # PATH FIX: src/characters/
        filename = f"src/characters/{clean_name}.json" 
        
        with open(filename, "r") as f:
            data = json.load(f)
            
        if "Local" in provider:
            return data.get("kokoro_voice", "af_bella")
        else:
            return data.get("elevenlabs_voice", "JBFqnCBsd6RMkjVDRZzb")
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return "af_bella"
    
def render_audio_line(line_index, line_data, provider):
    """Render a single line of audio. Used for parallel processing.
    
    Args:
        line_index: Index of the line in the script
        line_data: Dict with 'speaker' and 'text' fields
        provider: Voice provider string
    
    Returns:
        Tuple of (line_index, audio_segment) or (line_index, None) on error
    """
    # Validate line is a dict
    if not isinstance(line_data, dict):
        voice_logger.warning(f"Line {line_index}: expected dict, got {type(line_data)}")
        print(f"⚠️ Skipping line {line_index}: expected dict, got {type(line_data)}")
        return (line_index, None)
    
    speaker = line_data.get("speaker", "System")
    text = line_data.get("text", "")
    
    if not text:
        voice_logger.warning(f"Line {line_index}: no text content")
        print(f"⚠️ Skipping line {line_index}: no text content")
        return (line_index, None)
    
    voice_id = get_voice_id(speaker, provider)
    print(f"   🎙️ {speaker}: {text[:50]}...")
    voice_logger.debug(f"Line {line_index} - {speaker} (voice_id={voice_id}): {text[:100]}...")
    
    filename = f"temp_{line_index}_{time.time()}.wav"
    
    try:
        start_time = time.time()
        
        if "Local" in provider:
            samples, sample_rate = kokoro.create(text, voice=voice_id, speed=1.0, lang="en-us")
            sf.write(filename, samples, sample_rate)
            duration_ms = (time.time() - start_time) * 1000
            log_audio_rendering(speaker, filename, duration_ms)
            voice_logger.debug(f"Kokoro rendered {speaker}: {len(samples)} samples @ {sample_rate}Hz")
        else:
            client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
            log_elevenlabs_request(text, voice_id)
            audio_gen = client.generate(text=text, voice=voice_id, model="eleven_turbo_v2")
            save(audio_gen, filename)
            duration_ms = (time.time() - start_time) * 1000
            file_size = os.path.getsize(filename)
            log_elevenlabs_response(filename, file_size)
            log_audio_rendering(speaker, filename, duration_ms)
            voice_logger.debug(f"ElevenLabs rendered {speaker}: {file_size} bytes")

        if os.path.exists(filename):
            segment = AudioSegment.from_wav(filename)
            os.remove(filename)
            return (line_index, segment)
        else:
            return (line_index, None)
            
    except Exception as e:
        voice_logger.error(f"Line {line_index}: {str(e)}")
        print(f"⚠️ Error rendering line {line_index}: {e}")
        # Clean up temp file if it exists
        if os.path.exists(filename):
            os.remove(filename)
        return (line_index, None)


def render_audio(script, provider="Local (Kokoro)", max_workers=4):
    """Render podcast script to audio with parallel processing.
    
    Args:
        script: List of line objects with 'speaker' and 'text' fields
        provider: Voice provider ('Local (Kokoro)' or 'Cloud (ElevenLabs)')
        max_workers: Maximum number of parallel workers (default: 4)
    
    Returns:
        Path to final MP3 file
    """
    print(f"🔊 Voice: Rendering audio using {provider} (parallel mode: {max_workers} workers)...")
    voice_logger.info(f"Starting parallel audio render with {provider}, max_workers={max_workers}")
    
    if "Local" in provider and kokoro is None:
        raise Exception("Kokoro failed to load. Check logs.")
    
    # Validate script format
    if not isinstance(script, list):
        voice_logger.error(f"Script format error: expected list, got {type(script)}")
        raise Exception(f"Script must be a list, got {type(script)}")
    
    voice_logger.debug(f"Script contains {len(script)} lines")
    
    # Parallel rendering
    audio_segments = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all lines for parallel processing
        future_to_index = {
            executor.submit(render_audio_line, i, line, provider): i 
            for i, line in enumerate(script)
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_index):
            line_index, segment = future.result()
            if segment is not None:
                audio_segments[line_index] = segment
    
    # Combine segments in correct order
    voice_logger.info(f"Combining {len(audio_segments)} audio segments in order...")
    combined_audio = AudioSegment.empty()
    
    for i in range(len(script)):
        if i in audio_segments:
            combined_audio += audio_segments[i] + AudioSegment.silent(duration=300)
        else:
            voice_logger.warning(f"Missing audio for line {i}, skipping")
    
    output_file = "final_episode.mp3"
    combined_audio.export(output_file, format="mp3")
    voice_logger.info(f"Audio render complete: {output_file}")
    return output_file