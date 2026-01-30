import os
import soundfile as sf
from kokoro_onnx import Kokoro
from elevenlabs import ElevenLabs, save
from pydub import AudioSegment

# Initialize Kokoro (Local)
# You need the .onnx model file and voices.json in your folder
# Download details: https://github.com/thewh1teagle/kokoro-onnx
try:
    kokoro = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
except:
    print("⚠️ Local Kokoro model not found. Local TTS will fail.")

def render_audio(script, provider="Local (Kokoro)"):
    print(f"🔊 Voice: Rendering audio using {provider}...")
    
    combined_audio = AudioSegment.empty()
    
    # 1. Generate Clips
    for i, line in enumerate(script):
        speaker = line["speaker"].lower()
        text = line["text"]
        
        filename = f"temp_{i}.wav"
        
        if "Local" in provider:
            # --- LOCAL (Kokoro) ---
            # Alex = 'af_bella' (or similar male voice if available), Sam = 'af_sarah'
            # Check your voices.json for available IDs
            voice_id = "am_michael" if "alex" in speaker else "bf_emma"
            
            samples, sample_rate = kokoro.create(text, voice=voice_id, speed=1.0, lang="en-us")
            sf.write(filename, samples, sample_rate)
            
        else:
            # --- CLOUD (ElevenLabs) ---
            client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
            
            # Use specific Voice IDs from ElevenLabs Dashboard
            voice_id = "JBFqnCBsd6RMkjVDRZzb" if "alex" in speaker else "XrExE9yKIg1WjnnlVkGX"
            
            audio_gen = client.generate(text=text, voice=voice_id, model="eleven_turbo_v2")
            save(audio_gen, filename)

        # 2. Stitch immediately
        segment = AudioSegment.from_wav(filename)
        combined_audio += segment + AudioSegment.silent(duration=300) # Pause between lines
        
        # Cleanup temp file
        os.remove(filename)

    # 3. Export
    output_file = "final_episode.mp3"
    combined_audio.export(output_file, format="mp3")
    return output_file