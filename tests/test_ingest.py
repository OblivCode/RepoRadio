"""
Unit tests for ingest.py module.

Tests URL validation, repository analysis logic,
and Daytona sandbox operations.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.ingest import validate_github_url, get_repo_content


class TestValidateGithubUrl:
    """Test GitHub URL validation and sanitization."""
    
    def test_validate_valid_https_url(self):
        """Test validation of standard HTTPS GitHub URL."""
        url = "https://github.com/owner/repo"
        result = validate_github_url(url)
        assert result == url
    
    def test_validate_valid_http_url(self):
        """Test validation of HTTP GitHub URL."""
        url = "http://github.com/owner/repo"
        result = validate_github_url(url)
        assert result == url
    
    def test_validate_url_with_trailing_slash(self):
        """Test validation of URL with trailing slash."""
        url = "https://github.com/owner/repo/"
        result = validate_github_url(url)
        assert result == url.strip()
    
    def test_validate_url_with_git_extension(self):
        """Test validation of URL with .git extension."""
        url = "https://github.com/owner/repo.git"
        result = validate_github_url(url)
        assert result == url
    
    def test_validate_url_with_hyphens_dots(self):
        """Test validation of URL with hyphens and dots in names."""
        url = "https://github.com/my-org.name/my-repo.name"
        result = validate_github_url(url)
        assert result == url
    
    def test_reject_non_github_url(self):
        """Test rejection of non-GitHub URLs."""
        urls = [
            "https://gitlab.com/owner/repo",
            "https://bitbucket.org/owner/repo",
            "https://example.com/owner/repo"
        ]
        
        for url in urls:
            with pytest.raises(ValueError, match="Invalid GitHub URL"):
                validate_github_url(url)
    
    def test_reject_malformed_url(self):
        """Test rejection of malformed GitHub URLs."""
        urls = [
            "github.com/owner/repo",  # Missing protocol
            "https://github.com/",     # Missing owner/repo
            "https://github.com/owner", # Missing repo
            "ftp://github.com/owner/repo"  # Wrong protocol
        ]
        
        for url in urls:
            with pytest.raises(ValueError, match="Invalid GitHub URL"):
                validate_github_url(url)
    
    def test_reject_urls_with_shell_metacharacters(self):
        """Test rejection of URLs containing dangerous shell characters."""
        dangerous_urls = [
            "https://github.com/owner/repo; rm -rf /",
            "https://github.com/owner/repo && echo hack",
            "https://github.com/owner/repo | cat /etc/passwd",
            "https://github.com/owner/repo`whoami`",
            "https://github.com/owner/repo$(ls)",
            "https://github.com/owner/repo\ncat secret"
        ]
        
        for url in dangerous_urls:
            with pytest.raises(ValueError, match="dangerous characters"):
                validate_github_url(url)
    
    def test_strip_whitespace(self):
        """Test that validation strips leading/trailing whitespace."""
        url = "  https://github.com/owner/repo  "
        result = validate_github_url(url)
        assert result == url.strip()


class TestGetRepoContent:
    """Test repository content fetching."""
    
    @patch("src.ingest.Daytona")
    def test_get_repo_content_success(self, mock_daytona_class):
        """Test successful repository analysis."""
        # Mock Daytona SDK
        mock_daytona = MagicMock()
        mock_daytona_class.return_value = mock_daytona
        
        # Mock sandbox
        mock_sandbox = MagicMock()
        mock_sandbox.id = "test-sandbox-123"
        mock_daytona.create.return_value = mock_sandbox
        
        # Mock process execution results
        clone_result = MagicMock()
        clone_result.exit_code = 0
        clone_result.result = ""
        
        readme_result = MagicMock()
        readme_result.result = "# Test Repo\nThis is a test."
        
        tree_result = MagicMock()
        tree_result.result = "repo/\nrepo/main.py\nrepo/README.md"
        
        mock_sandbox.process.exec.side_effect = [
            clone_result,
            readme_result,
            tree_result
        ]
        
        with patch("src.ingest.log_daytona_sandbox"), \
             patch("src.ingest.log_git_clone"):
            
            result = get_repo_content("https://github.com/test/repo")
        
        # Verify sandbox was created and deleted
        mock_daytona.create.assert_called_once()
        mock_daytona.delete.assert_called_once_with(mock_sandbox)
        
        # Verify result contains expected content
        assert "README CONTENT:" in result
        assert "FILE STRUCTURE:" in result
        assert "Test Repo" in result
    
    @patch("src.ingest.Daytona")
    def test_get_repo_content_git_clone_failure(self, mock_daytona_class):
        """Test handling of git clone failure."""
        mock_daytona = MagicMock()
        mock_daytona_class.return_value = mock_daytona
        
        mock_sandbox = MagicMock()
        mock_daytona.create.return_value = mock_sandbox
        
        # Mock failed git clone
        clone_result = MagicMock()
        clone_result.exit_code = 1
        clone_result.result = "fatal: repository not found"
        mock_sandbox.process.exec.return_value = clone_result
        
        with patch("src.ingest.log_daytona_sandbox"), \
             patch("src.ingest.log_git_clone"), \
             patch("src.ingest.log_daytona_error"):
            
            result = get_repo_content("https://github.com/test/nonexistent")
        
        assert "Error cloning:" in result
        assert "repository not found" in result
    
    def test_get_repo_content_invalid_url(self):
        """Test that invalid URLs are rejected before Daytona call."""
        result = get_repo_content("https://example.com/not/github")
        
        assert "URL validation failed" in result
    
    @patch("src.ingest.Daytona")
    def test_get_repo_content_deep_mode_todo(self, mock_daytona_class):
        """Test that deep_mode parameter is acknowledged but not implemented."""
        mock_daytona = MagicMock()
        mock_daytona_class.return_value = mock_daytona
        
        mock_sandbox = MagicMock()
        mock_sandbox.id = "test-sandbox"
        mock_daytona.create.return_value = mock_sandbox
        
        clone_result = MagicMock()
        clone_result.exit_code = 0
        readme_result = MagicMock()
        readme_result.result = "README"
        tree_result = MagicMock()
        tree_result.result = "files"
        
        mock_sandbox.process.exec.side_effect = [clone_result, readme_result, tree_result]
        
        with patch("src.ingest.log_daytona_sandbox"), \
             patch("src.ingest.log_git_clone"):
            
            # Call with deep_mode=True
            result = get_repo_content("https://github.com/test/repo", deep_mode=True)
        
        # Should complete successfully (deep mode just logs for now)
        assert "README CONTENT:" in result


class TestPlanResearch:
    """Test plan_research function (currently unused)."""
    
    @patch("src.ingest.requests.post")
    @patch("src.ingest.get_host_ip")
    def test_plan_research_returns_file_list(self, mock_ip, mock_post):
        """Test that plan_research returns list of priority files."""
        from src.ingest import plan_research
        
        mock_ip.return_value = "localhost"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": '["src/main.py", "config.yaml", "README.md"]'
        }
        mock_post.return_value = mock_response
        
        result = plan_research("file tree data", "Local (Ollama)")
        
        assert isinstance(result, list)
        assert len(result) <= 3  # Should return up to 3 files
    
    @patch("src.ingest.requests.post")
    @patch("src.ingest.get_host_ip")
    def test_plan_research_handles_errors(self, mock_ip, mock_post):
        """Test that plan_research returns empty list on error."""
        from src.ingest import plan_research
        
        mock_ip.return_value = "localhost"
        mock_post.side_effect = Exception("Connection failed")
        
        result = plan_research("file tree", "Local (Ollama)")
        
        assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
