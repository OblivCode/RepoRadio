"""
Sound effects and audio enhancement for RepoRadio.
Handles dynamic SFX triggers based on context.
"""
from pathlib import Path
from pydub import AudioSegment
from debug_logger import voice_logger


class SoundEffectsLibrary:
    """Manages sound effects library for context-aware audio enhancement."""
    
    def __init__(self):
        self.assets_dir = Path(__file__).parent / "assets"
        self.sfx_cache = {}
    
    def load_sfx(self, sfx_name):
        """Load a sound effect from assets folder."""
        if sfx_name in self.sfx_cache:
            return self.sfx_cache[sfx_name]
        
        sfx_path = self.assets_dir / f"{sfx_name}.mp3"
        if not sfx_path.exists():
            sfx_path = self.assets_dir / f"{sfx_name}.wav"
        
        if sfx_path.exists():
            try:
                sfx = AudioSegment.from_file(sfx_path)
                self.sfx_cache[sfx_name] = sfx
                voice_logger.debug(f"Loaded SFX: {sfx_name}")
                return sfx
            except Exception as e:
                voice_logger.error(f"Failed to load SFX {sfx_name}: {str(e)}")
                return None
        
        voice_logger.debug(f"SFX not found: {sfx_name}")
        return None
    
    def overlay_sfx_on_segment(self, audio_segment, sfx_name, position_ms=0):
        """
        Overlay a sound effect on an audio segment.
        
        Args:
            audio_segment: AudioSegment to add effect to
            sfx_name: Name of the sound effect file (without extension)
            position_ms: Position in ms to overlay the effect
        
        Returns:
            AudioSegment with effect overlaid
        """
        sfx = self.load_sfx(sfx_name)
        if sfx is None:
            return audio_segment
        
        try:
            result = audio_segment.overlay(sfx, position=position_ms)
            voice_logger.debug(f"Overlaid SFX '{sfx_name}' at {position_ms}ms")
            return result
        except Exception as e:
            voice_logger.error(f"Failed to overlay SFX: {str(e)}")
            return audio_segment
    
    def detect_and_add_sfx(self, script_line, audio_segment):
        """
        Analyze script text and add appropriate sound effects.
        
        Args:
            script_line: Dict with 'speaker' and 'text' keys
            audio_segment: AudioSegment to potentially add effects to
        
        Returns:
            AudioSegment (potentially with SFX added)
        """
        text = script_line.get("text", "").lower()
        speaker = script_line.get("speaker", "")
        
        # Detect criticism/negative reactions (Sam, Marcus)
        if any(word in text for word in ["terrible", "awful", "horrible", "wrong", "hate", "nightmare"]):
            if speaker in ["Sam", "Marcus"]:
                return self.overlay_sfx_on_segment(audio_segment, "gavel", position_ms=100)
        
        # Detect excitement/celebration
        if any(word in text for word in ["amazing", "awesome", "perfect", "brilliant", "love it"]):
            return self.overlay_sfx_on_segment(audio_segment, "applause", position_ms=len(audio_segment) - 500)
        
        # Detect security/danger mentions
        if any(word in text for word in ["vulnerability", "security flaw", "exploit", "hack"]):
            if speaker == "Marcus":
                return self.overlay_sfx_on_segment(audio_segment, "alert", position_ms=50)
        
        # Detect tech jargon overload
        if any(word in text for word in ["kubernetes", "microservices", "blockchain", "quantum"]):
            return self.overlay_sfx_on_segment(audio_segment, "tech_whoosh", position_ms=0)
        
        # Return unmodified if no triggers detected
        return audio_segment


# Singleton instance
sfx_library = SoundEffectsLibrary()


def add_context_aware_sfx(script, audio_segments):
    """
    Add sound effects to audio segments based on script context.
    
    Args:
        script: List of script line dicts
        audio_segments: Dict of index -> AudioSegment
    
    Returns:
        Dict of index -> AudioSegment (with SFX added where appropriate)
    """
    enhanced_segments = {}
    
    for i, line in enumerate(script):
        if i in audio_segments:
            enhanced_segments[i] = sfx_library.detect_and_add_sfx(line, audio_segments[i])
        else:
            enhanced_segments[i] = audio_segments.get(i)
    
    return enhanced_segments
