"""
Audio mixing module for RepoRadio.
Handles background music overlay, crossfading, and audio effects.
"""
import os
import random
from pathlib import Path
from pydub import AudioSegment
from debug_logger import voice_logger


def get_random_background_track():
    """Get a random background music track from src/music/ folder."""
    music_dir = Path(__file__).parent.parent / "music"
    
    if not music_dir.exists():
        voice_logger.warning("Music directory not found, skipping background music")
        return None
    
    # Find all audio files (mp3, wav, ogg)
    audio_files = list(music_dir.glob("*.mp3")) + list(music_dir.glob("*.wav")) + list(music_dir.glob("*.ogg"))
    
    if not audio_files:
        voice_logger.warning("No music files found in src/music/, skipping background music")
        return None
    
    selected_track = random.choice(audio_files)
    voice_logger.info(f"Selected background track: {selected_track.name}")
    return str(selected_track)


def overlay_background_music(dialogue_audio, bg_track_path=None, volume_reduction_db=20):
    """
    Overlay background music on dialogue audio.
    
    Args:
        dialogue_audio: AudioSegment of the dialogue
        bg_track_path: Path to background music file (None = auto-select random)
        volume_reduction_db: How much to reduce background music volume (default: 20dB)
    
    Returns:
        AudioSegment with background music overlaid
    """
    if bg_track_path is None:
        bg_track_path = get_random_background_track()
    
    if bg_track_path is None:
        voice_logger.warning("No background music available, returning dialogue only")
        return dialogue_audio
    
    try:
        # Load background music
        bg_music = AudioSegment.from_file(bg_track_path)
        voice_logger.debug(f"Background music loaded: {len(bg_music)}ms, dialogue: {len(dialogue_audio)}ms")
        
        # Reduce background music volume so it doesn't overpower dialogue
        bg_music = bg_music - volume_reduction_db
        
        # Loop or trim background music to match dialogue length
        dialogue_len = len(dialogue_audio)
        bg_len = len(bg_music)
        
        if bg_len < dialogue_len:
            # Loop the music with crossfade at loop points for seamless playback
            loops_needed = (dialogue_len // bg_len) + 1
            looped_bg = bg_music
            for _ in range(loops_needed - 1):
                looped_bg = looped_bg.append(bg_music, crossfade=1000)  # 1 second crossfade
            bg_music = looped_bg[:dialogue_len]
            voice_logger.debug(f"Looped background music {loops_needed} times")
        else:
            # Trim and fade out
            bg_music = bg_music[:dialogue_len]
            bg_music = bg_music.fade_out(3000)  # 3 second fade out at the end
            voice_logger.debug("Trimmed background music to dialogue length")
        
        # Overlay the background music
        mixed_audio = dialogue_audio.overlay(bg_music)
        voice_logger.info(f"Background music overlaid successfully ({volume_reduction_db}dB reduction)")
        
        return mixed_audio
        
    except Exception as e:
        voice_logger.error(f"Failed to overlay background music: {str(e)}")
        return dialogue_audio  # Return original on error


def add_crossfade_between_segments(segments, crossfade_ms=200):
    """
    Combine audio segments with crossfade between them.
    
    Args:
        segments: List of AudioSegment objects
        crossfade_ms: Crossfade duration in milliseconds
    
    Returns:
        Combined AudioSegment with crossfades
    """
    if not segments:
        return AudioSegment.empty()
    
    if len(segments) == 1:
        return segments[0]
    
    combined = segments[0]
    
    for i in range(1, len(segments)):
        # Add crossfade between segments for smoother transitions
        combined = combined.append(segments[i], crossfade=crossfade_ms)
        voice_logger.debug(f"Added segment {i} with {crossfade_ms}ms crossfade")
    
    voice_logger.info(f"Combined {len(segments)} segments with crossfading")
    return combined


def add_intro_outro(dialogue_audio, intro_path=None, outro_path=None):
    """
    Add intro and/or outro jingles to the podcast.
    
    Args:
        dialogue_audio: AudioSegment of the main dialogue
        intro_path: Path to intro jingle (None = use default)
        outro_path: Path to outro jingle (None = use default)
    
    Returns:
        AudioSegment with intro/outro added
    """
    assets_dir = Path(__file__).parent / "assets"
    
    # Default intro/outro paths
    if intro_path is None:
        intro_path = assets_dir / "intro_jingle.mp3"
    if outro_path is None:
        outro_path = assets_dir / "outro_jingle.mp3"
    
    result = dialogue_audio
    
    # Add intro if it exists
    if os.path.exists(intro_path):
        try:
            intro = AudioSegment.from_file(intro_path)
            result = intro + AudioSegment.silent(duration=500) + result
            voice_logger.info("Added intro jingle")
        except Exception as e:
            voice_logger.warning(f"Failed to add intro jingle: {str(e)}")
    else:
        voice_logger.debug(f"No intro jingle found at {intro_path}")
    
    # Add outro if it exists
    if os.path.exists(outro_path):
        try:
            outro = AudioSegment.from_file(outro_path)
            result = result + AudioSegment.silent(duration=500) + outro
            voice_logger.info("Added outro jingle")
        except Exception as e:
            voice_logger.warning(f"Failed to add outro jingle: {str(e)}")
    else:
        voice_logger.debug(f"No outro jingle found at {outro_path}")
    
    return result


def add_ad_break_transition(dialogue_audio, ad_audio, ad_position=None):
    """
    Insert an ad break into the dialogue at a specific position.
    
    Args:
        dialogue_audio: AudioSegment of the main dialogue
        ad_audio: AudioSegment of the ad break
        ad_position: Position in ms to insert ad (None = middle)
    
    Returns:
        AudioSegment with ad break inserted
    """
    if ad_position is None:
        ad_position = len(dialogue_audio) // 2
    
    # Split dialogue at ad position
    before_ad = dialogue_audio[:ad_position]
    after_ad = dialogue_audio[ad_position:]
    
    # Add transition sound if available
    assets_dir = Path(__file__).parent / "assets"
    transition_path = assets_dir / "ad_transition.mp3"
    
    if os.path.exists(transition_path):
        try:
            transition = AudioSegment.from_file(transition_path)
            result = before_ad + transition + ad_audio + transition + after_ad
            voice_logger.info("Added ad break with transition sounds")
        except Exception as e:
            voice_logger.warning(f"Failed to add transition sound: {str(e)}")
            result = before_ad + AudioSegment.silent(duration=300) + ad_audio + AudioSegment.silent(duration=300) + after_ad
    else:
        # No transition sound, use silence
        result = before_ad + AudioSegment.silent(duration=300) + ad_audio + AudioSegment.silent(duration=300) + after_ad
        voice_logger.debug("Added ad break with silence (no transition sound)")
    
    return result
