"""
Test configuration and shared fixtures for pytest.
"""

import sys
from pathlib import Path

# Add src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
