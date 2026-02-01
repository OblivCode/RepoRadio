"""
Unit tests for brain.py module.

Tests character loading, script generation with 1-3 hosts,
and prompt template replacement logic.
"""

import pytest
import json
import os
from unittest.mock import patch, mock_open, MagicMock
from src.brain import load_character, generate_script, BASE_PROMPT


class TestLoadCharacter:
    """Test character loading functionality."""
    
    def test_load_character_success(self):
        """Test successful character loading."""
        mock_data = {
            "name": "Alex",
            "description": "The Hype Man",
            "kokoro_voice": "am_michael",
            "elevenlabs_voice": "test_voice_id"
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
            with patch("src.brain.log_character_load"):
                result = load_character("Alex")
                
        assert result["name"] == "Alex"
        assert result["description"] == "The Hype Man"
        assert "kokoro_voice" in result
    
    def test_load_character_file_not_found(self):
        """Test character loading when file doesn't exist."""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            with patch("src.brain.log_character_load"):
                result = load_character("NonExistent")
        
        # Should return fallback character
        assert result["name"] == "NonExistent"
        assert result["description"] == "A standard radio host."
    
    def test_load_character_invalid_json(self):
        """Test character loading with invalid JSON."""
        with patch("builtins.open", mock_open(read_data="invalid json")):
            with patch("src.brain.log_character_load"):
                result = load_character("BadJson")
        
        # Should return fallback character
        assert result["name"] == "BadJson"
        assert result["description"] == "A standard radio host."


class TestGenerateScript:
    """Test script generation with variable hosts."""
    
    @patch("src.brain.requests.post")
    @patch("src.brain.load_character")
    @patch("src.brain.get_host_ip")
    def test_generate_script_one_host(self, mock_ip, mock_load_char, mock_post):
        """Test script generation with 1 host (monologue)."""
        # Mock character data
        mock_load_char.return_value = {
            "name": "Alex",
            "description": "The Hype Man"
        }
        mock_ip.return_value = "localhost"
        
        # Mock Ollama response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": '[{"speaker": "Alex", "text": "Welcome!"}]'
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = generate_script("Test repo content", ["Alex"], "Local (Ollama)")
        
        assert isinstance(result, list)
        assert len(result) > 0
        mock_load_char.assert_called_once_with("Alex")
    
    @patch("src.brain.requests.post")
    @patch("src.brain.load_character")
    @patch("src.brain.get_host_ip")
    def test_generate_script_two_hosts(self, mock_ip, mock_load_char, mock_post):
        """Test script generation with 2 hosts (dialogue)."""
        # Mock character data
        mock_load_char.side_effect = [
            {"name": "Alex", "description": "The Hype Man"},
            {"name": "Marcus", "description": "The Skeptic"}
        ]
        mock_ip.return_value = "localhost"
        
        # Mock Ollama response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": '[{"speaker": "Alex", "text": "Hi!"}, {"speaker": "Marcus", "text": "Hello!"}]'
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = generate_script("Test content", ["Alex", "Marcus"], "Local (Ollama)")
        
        assert isinstance(result, list)
        assert mock_load_char.call_count == 2
    
    @patch("src.brain.requests.post")
    @patch("src.brain.load_character")
    @patch("src.brain.get_host_ip")
    def test_generate_script_three_hosts(self, mock_ip, mock_load_char, mock_post):
        """Test script generation with 3 hosts (panel discussion)."""
        # Mock character data
        mock_load_char.side_effect = [
            {"name": "Alex", "description": "The Hype Man"},
            {"name": "Marcus", "description": "The Skeptic"},
            {"name": "Sam", "description": "The Analyst"}
        ]
        mock_ip.return_value = "localhost"
        
        # Mock Ollama response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": '[{"speaker": "Alex", "text": "A"}, {"speaker": "Marcus", "text": "B"}, {"speaker": "Sam", "text": "C"}]'
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = generate_script("Test content", ["Alex", "Marcus", "Sam"], "Local (Ollama)")
        
        assert isinstance(result, list)
        assert mock_load_char.call_count == 3
    
    @patch("src.brain.load_character")
    def test_prompt_template_replacement(self, mock_load_char):
        """Test that HOST_DEFINITIONS placeholder is correctly replaced."""
        mock_load_char.side_effect = [
            {"name": "Alex", "description": "The Hype Man"},
            {"name": "Marcus", "description": "The Skeptic"}
        ]
        
        # Build the prompt manually like generate_script does
        host_characters = [mock_load_char("Alex"), mock_load_char("Marcus")]
        host_defs = [f"- {h['name'].upper()}: {h['description']}" for h in host_characters]
        all_host_defs = "\n".join(host_defs)
        system_prompt = BASE_PROMPT.replace("HOST_DEFINITIONS", all_host_defs)
        
        # Verify replacement worked
        assert "HOST_DEFINITIONS" not in system_prompt
        assert "- ALEX: The Hype Man" in system_prompt
        assert "- MARCUS: The Skeptic" in system_prompt


class TestPromptTemplate:
    """Test BASE_PROMPT template structure."""
    
    def test_base_prompt_has_placeholder(self):
        """Verify BASE_PROMPT contains HOST_DEFINITIONS placeholder."""
        assert "HOST_DEFINITIONS" in BASE_PROMPT
    
    def test_base_prompt_has_monologue_instructions(self):
        """Verify prompt handles 1-host monologue case."""
        assert "one host" in BASE_PROMPT.lower()
        assert "monologue" in BASE_PROMPT.lower()
    
    def test_base_prompt_has_multiple_host_instructions(self):
        """Verify prompt handles multiple hosts case."""
        assert "multiple hosts" in BASE_PROMPT.lower()
        assert "banter" in BASE_PROMPT.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
