import os
import json
import requests
import subprocess
from openai import OpenAI

# Updated Prompt: Enforces education and explanation over pure banter
BASE_PROMPT = """
You are the producer of 'RepoRadio', a podcast where expert developers review GitHub projects.
Your goal is to write a 3-minute script that is ENTERTAINING but highly EDUCATIONAL.

The Hosts are:
HOST_DEFINITIONS

Instructions:
- If multiple hosts are present, they should banter and bounce ideas off each other.
- If only one host is present, they should deliver an engaging monologue/deep-dive.
- Do NOT just say "this code is good/bad". Explain *WHY*.
- Explain technical concepts found in the "Repo Analysis".
- If "DEEP DIVE CODE" is present, quote specific lines.
- Format the output as a JSON list of objects.

Format: Return ONLY a valid JSON list: [{"speaker": "HostName", "text": "..."}]
"""

# ... (Planner Prompt stays the same) ...
PLANNER_PROMPT = """
You are a Senior Architect analyzing a file tree.
Identify up to 3 files that are most critical to understanding how this project works.
- Look for entry points (main.rs, index.ts), core logic, or funny config files.
- Ignore documentation, licenses, and lockfiles.
Format: Return ONLY a JSON list of strings. Example: ["src/main.rs", "config.toml"]
"""

def get_host_ip():
    # Hardcoded for reliability as requested
    if os.getenv("OLLAMA_IP"): return os.getenv("OLLAMA_IP")
    return "192.168.1.119"

def load_character(char_name):
    """Reads the JSON file for a specific character from src/characters."""
    try:
        # PATH FIX: Now points to src/characters/
        filename = f"src/characters/{char_name.lower()}.json"
        with open(filename, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Could not load character {char_name}: {e}")
        return {"name": char_name, "description": "A standard radio host."}

def plan_research(file_tree, provider="Local (Ollama)"):
    host_ip = get_host_ip()
    if "Local" in provider:
        url_base = f"http://{host_ip}:11434/api/generate"
        try:
            prompt = f"{PLANNER_PROMPT}\n\nFile Structure:\n{file_tree}\n\nRespond with ONLY valid JSON."
            payload = {"model": "llama3.1:8b", "prompt": prompt, "stream": False, "format": "json"}
            res = requests.post(url_base, json=payload, timeout=15)
            return json.loads(res.json()["response"])
        except:
            return []
    else:
        return []

def generate_script(repo_content, host1, host2, provider="Local (Ollama)"):
    print(f"🧠 Brain: Generating script for {host1} vs {host2}...")
    
    # 1. Load Personality Data
    h1_data = load_character(host1)
    h2_data = load_character(host2)
    
    # 2. Build Prompt
    h1_def = f"- {h1_data['name'].upper()}: {h1_data['description']}"
    h2_def = f"- {h2_data['name'].upper()}: {h2_data['description']}"
    system_prompt = BASE_PROMPT.replace("HOST_1_DEF", h1_def).replace("HOST_2_DEF", h2_def)
    
    host_ip = get_host_ip()
    
    if "Local" in provider:
        url_base = f"http://{host_ip}:11434/api/generate"
        try:
            prompt = f"{system_prompt}\n\nRepo Analysis:\n{repo_content}\n\nRespond with ONLY valid JSON."
            # Using llama3.1:8b for technical explanation
            payload = {"model": "llama3.1:8b", "prompt": prompt, "stream": False}
            
            response = requests.post(url_base, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            response_text = data.get("response", "")
            
            # Parse the JSON response
            parsed = json.loads(response_text)
            
            # Validate it's a list of dictionaries
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict) and "script" in parsed:
                return parsed["script"]
            else:
                return [{"speaker": "System", "text": f"Unexpected response format: {parsed}"}]
                
        except json.JSONDecodeError as e:
            return [{"speaker": "System", "text": f"JSON Parse Error: {str(e)}"}]
        except Exception as e:
            return [{"speaker": "System", "text": f"Error: {str(e)}"}]
    else:
        # Cloud logic (same as before)
        pass