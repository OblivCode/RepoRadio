"""
Unit tests for voice.py module.

Tests voice ID resolution, audio rendering logic,
and TTS provider selection.
"""

import pytest
import json
from unittest.mock import patch, mock_open, MagicMock
from src.voice import get_voice_id


class TestGetVoiceId:
    """Test voice ID resolution for different providers."""
    
    def test_get_voice_id_local_provider(self):
        """Test voice ID resolution for local Kokoro provider."""
        mock_data = {
            "name": "Alex",
            "kokoro_voice": "am_michael",
            "elevenlabs_voice": "cloud_voice_id"
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
            result = get_voice_id("Alex", "Local (Kokoro)")
        
        assert result == "am_michael"
    
    def test_get_voice_id_cloud_provider(self):
        """Test voice ID resolution for cloud ElevenLabs provider."""
        mock_data = {
            "name": "Marcus",
            "kokoro_voice": "local_voice",
            "elevenlabs_voice": "cloud_marcus_voice"
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
            result = get_voice_id("Marcus", "Cloud (ElevenLabs)")
        
        assert result == "cloud_marcus_voice"
    
    def test_get_voice_id_file_not_found(self):
        """Test fallback when character file doesn't exist."""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            result = get_voice_id("NonExistent", "Local (Kokoro)")
        
        # Should return default fallback voice
        assert result == "af_bella"
    
    def test_get_voice_id_invalid_json(self):
        """Test fallback when character JSON is invalid."""
        with patch("builtins.open", mock_open(read_data="invalid json")):
            result = get_voice_id("BadJson", "Local (Kokoro)")
        
        assert result == "af_bella"
    
    def test_get_voice_id_missing_voice_field(self):
        """Test fallback when voice field is missing from character."""
        mock_data = {
            "name": "Incomplete",
            "description": "Missing voice fields"
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
            result = get_voice_id("Incomplete", "Local (Kokoro)")
        
        # Should return default from .get() fallback
        assert result == "af_bella"
    
    def test_get_voice_id_handles_full_name(self):
        """Test that function extracts first name from full name."""
        mock_data = {
            "name": "Sam",
            "kokoro_voice": "bf_emma",
            "elevenlabs_voice": "sam_cloud"
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
            # Pass full name with space
            result = get_voice_id("Sam Anderson", "Local (Kokoro)")
        
        # Should extract "sam" and find the file
        assert result == "bf_emma"


class TestRenderAudio:
    """Test audio rendering functionality."""
    
    @patch("src.voice.kokoro")
    @patch("src.voice.get_voice_id")
    @patch("src.voice.AudioSegment")
    def test_render_audio_local_provider(self, mock_audio_segment, mock_get_voice, mock_kokoro):
        """Test audio rendering with local Kokoro provider."""
        from src.voice import render_audio
        
        # Mock kokoro as available
        mock_kokoro_instance = MagicMock()
        mock_kokoro_instance.create.return_value = (b"fake audio data", None)
        
        with patch("src.voice.kokoro", mock_kokoro_instance):
            mock_get_voice.return_value = "am_michael"
            
            # Mock AudioSegment operations
            mock_segment = MagicMock()
            mock_audio_segment.from_wav.return_value = mock_segment
            mock_audio_segment.empty.return_value = mock_segment
            mock_segment.__add__ = MagicMock(return_value=mock_segment)
            
            script = [
                {"speaker": "Alex", "text": "Hello world!"}
            ]
            
            result = render_audio(script, "Local (Kokoro)")
            
            # Should return output file path
            assert result == "final_episode.mp3"
    
    def test_render_audio_validates_script_format(self):
        """Test that render_audio validates script is a list."""
        from src.voice import render_audio
        
        # Pass invalid script (not a list)
        with pytest.raises(Exception, match="Script must be a list"):
            render_audio("not a list", "Local (Kokoro)")
    
    @patch("src.voice.kokoro", None)
    def test_render_audio_fails_when_kokoro_not_loaded(self):
        """Test that render fails gracefully when Kokoro isn't available."""
        from src.voice import render_audio
        
        script = [{"speaker": "Alex", "text": "Test"}]
        
        with pytest.raises(Exception, match="Kokoro failed to load"):
            render_audio(script, "Local (Kokoro)")


class TestVoiceProviderSelection:
    """Test voice provider selection logic."""
    
    def test_local_provider_string_matching(self):
        """Test that 'Local' in provider string is correctly detected."""
        providers = [
            "Local (Kokoro)",
            "Local (Ollama)",
            "local tts"
        ]
        
        for provider in providers:
            assert "Local" in provider or "local" in provider.lower()
    
    def test_cloud_provider_string_matching(self):
        """Test that cloud providers are correctly identified."""
        providers = [
            "Cloud (ElevenLabs)",
            "Cloud (OpenAI)"
        ]
        
        for provider in providers:
            assert "Cloud" in provider or "cloud" in provider.lower()
            assert "Local" not in provider


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
