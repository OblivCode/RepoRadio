import os
import json
import requests
import subprocess
import time
from openai import OpenAI
from debug_logger import brain_logger, log_ollama_request, log_ollama_response, log_ollama_error, log_character_load

# Updated Prompt: Enforces education and explanation over pure banter
BASE_PROMPT = """
You are the producer of 'RepoRadio', a podcast where expert developers review GitHub projects.
Your goal is to write a 3-minute script that is ENTERTAINING but highly EDUCATIONAL.

The Hosts are:
HOST_DEFINITIONS

Instructions:
- Generate EXACTLY 8-12 lines of dialogue (conversation turns).
- If multiple hosts are present, they should banter and bounce ideas off each other.
- Each host should speak multiple times, alternating naturally.
- If only one host is present, break their monologue into 8-12 segments.
- Do NOT just say "this code is good/bad". Explain *WHY*.
- Explain technical concepts found in the "Repo Analysis".
- If "DEEP DIVE CODE" is present, quote specific lines.
- Make it conversational with reactions, questions, and follow-ups.

CRITICAL: Return a JSON array with 8-12 objects minimum. Each object has "speaker" and "text".
Example:
[
  {"speaker": "Alex", "text": "Welcome to RepoRadio! Today we're diving into this awesome project."},
  {"speaker": "Casey", "text": "Oh wow, I'm excited! What does it do?"},
  {"speaker": "Alex", "text": "It's a development environment manager, and it's fire!"},
  {"speaker": "Casey", "text": "Cool! How does it work under the hood?"},
  {"speaker": "Alex", "text": "Great question! Let me break down the architecture..."}
]

Start with [ and end with ]. Do NOT stop after 1-2 lines. Generate the full conversation.
"""

# ... (Planner Prompt stays the same) ...
PLANNER_PROMPT = """
You are a Senior Architect analyzing a file tree.
Identify up to 3 files that are most critical to understanding how this project works.
- Look for entry points (main.rs, index.ts), core logic, or funny config files.
- Ignore documentation, licenses, and lockfiles.

CRITICAL: Return ONLY a JSON array (list) of filename strings.
Example: ["src/main.py", "config.yaml", "README.md"]
Do NOT wrap in an object. Start with [ and end with ].
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
            data = json.load(f)
            log_character_load(char_name, True)
            return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"⚠️ Could not load character {char_name}: {e}")
        log_character_load(char_name, False, str(e))
        return {"name": char_name, "description": "A standard radio host."}

def plan_research(file_tree, provider="Local (Ollama)"):
    """Use AI to identify 3 most important files from file tree."""
    host_ip = get_host_ip()
    if "Local" in provider:
        url_base = f"http://{host_ip}:11434/api/generate"
        try:
            prompt = f"{PLANNER_PROMPT}\n\nFile Structure:\n{file_tree}\n\nRespond with ONLY valid JSON."
            payload = {"model": "llama3.1:8b", "prompt": prompt, "stream": False, "format": "json"}
            brain_logger.debug(f"Plan research request to {url_base}")
            res = requests.post(url_base, json=payload, timeout=20)
            res.raise_for_status()
            
            response_data = res.json()
            response_text = response_data.get("response", "").strip()
            
            if not response_text:
                brain_logger.warning("Plan research got empty response")
                return []
            
            brain_logger.debug(f"Plan research raw response: {response_text[:200]}")
            parsed = json.loads(response_text)
            
            # Handle wrapped responses (e.g., {"files": [...]} or {"list": [...]})
            file_list = None
            if isinstance(parsed, list):
                file_list = parsed
            elif isinstance(parsed, dict):
                brain_logger.debug(f"Plan research got dict with keys: {list(parsed.keys())}")
                brain_logger.debug(f"Full dict: {parsed}")
                
                # Try common wrapper keys
                for key in ["files", "list", "priority_files", "important_files", "paths", "result"]:
                    if key in parsed:
                        value = parsed[key]
                        if isinstance(value, list):
                            file_list = value
                            brain_logger.debug(f"Extracted file list from '{key}' wrapper")
                            break
                        elif isinstance(value, str):
                            # Sometimes returns comma-separated string
                            file_list = [f.strip() for f in value.split(',')]
                            brain_logger.debug(f"Split string from '{key}' into list")
                            break
            
            if file_list and len(file_list) > 0:
                brain_logger.info(f"Plan research identified {len(file_list)} files: {file_list}")
                return file_list
            else:
                brain_logger.warning(f"Plan research returned unexpected format: {type(parsed)}, value: {parsed}")
                return []
                
        except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError) as e:
            brain_logger.error(f"Plan research failed: {str(e)}")
            return []
    else:
        return []

def generate_script(repo_content, host_names, provider="Local (Ollama)"):
    """Generate podcast script for 1-3 hosts.
    
    Args:
        repo_content: Repository analysis text
        host_names: List of 1-3 character names
        provider: AI provider string
    
    Returns:
        List of script objects with speaker and text fields
    """
    hosts_str = ', '.join(host_names)
    print(f"🧠 Brain: Generating script for {hosts_str}...")
    brain_logger.info(f"Generating script for hosts: {hosts_str} | Provider: {provider}")
    
    # 1. Load Personality Data for all hosts
    host_characters = [load_character(name) for name in host_names]
    
    # 2. Build Prompt with dynamic host definitions
    host_defs = [f"- {h['name'].upper()}: {h['description']}" for h in host_characters]
    all_host_defs = "\n".join(host_defs)
    system_prompt = BASE_PROMPT.replace("HOST_DEFINITIONS", all_host_defs)
    
    host_ip = get_host_ip()
    
    if "Local" in provider:
        url_base = f"http://{host_ip}:11434/api/generate"
        
        models_to_try = ["llama3.1:8b"]
        
        for attempt, model in enumerate(models_to_try, 1):
            try:
                # Truncate content for reliability (allow more with deep mode)
                max_chars = 3000 if "DEEP DIVE CODE" in repo_content else 2000
                content_preview = repo_content[:max_chars] if len(repo_content) > max_chars else repo_content
                prompt = f"{system_prompt}\n\nRepo Analysis:\n{content_preview}\n\nRespond with ONLY valid JSON."
                
                payload = {
                    "model": model, 
                    "prompt": prompt, 
                    "stream": False, 
                    "format": "json",
                    "options": {
                        "num_predict": 2000,  # Allow longer responses
                        "temperature": 0.7    # Slight creativity for variety
                    }
                }
                
                brain_logger.debug(f"Attempt {attempt}/{len(models_to_try)}: Trying model {model}")
                log_ollama_request(model, prompt, url_base)
                
                start_time = time.time()
                response = requests.post(url_base, json=payload, timeout=60)
                response.raise_for_status()
                
                data = response.json()
                response_text = data.get("response", "").strip()
                
                duration_ms = (time.time() - start_time) * 1000
                
                # Check for empty response
                if not response_text:
                    brain_logger.warning(f"Empty response from {model} at {url_base}")
                    brain_logger.debug(f"Full response object: {data}")
                    continue  # Try next model
                
                log_ollama_response(response_text, duration_ms)
                
                # Try to parse JSON
                try:
                    parsed = json.loads(response_text)
                except json.JSONDecodeError as e:
                    brain_logger.warning(f"JSON parse error from {model}: {str(e)}")
                    brain_logger.debug(f"Response text: {response_text[:200]}")
                    continue  # Try next model
                
                # Validate it's a list of dictionaries (handle wrapped responses)
                script_data = None
                if isinstance(parsed, list):
                    script_data = parsed
                elif isinstance(parsed, dict):
                    # Check if it's a single script line (has speaker and text keys)
                    if "speaker" in parsed and "text" in parsed:
                        brain_logger.debug("Received single script line, wrapping in list")
                        script_data = [parsed]  # Wrap single line in array
                    else:
                        # Try common wrapper keys
                        for key in ["script", "podcast", "lines", "dialogue", "conversation"]:
                            if key in parsed and isinstance(parsed[key], list):
                                script_data = parsed[key]
                                brain_logger.debug(f"Extracted script from '{key}' wrapper")
                                break
                        
                        # If still no script found, log it
                        if script_data is None:
                            brain_logger.warning(f"Response is dict but no recognized script key. Keys: {list(parsed.keys())}")
                            brain_logger.debug(f"Full parsed response: {parsed}")
                            continue
                
                if script_data and len(script_data) > 0:
                    brain_logger.info(f"✅ Successfully generated script with {model} ({len(script_data)} lines)")
                    return script_data
                else:
                    brain_logger.warning(f"Unexpected response format from {model}: {type(parsed)}")
                    continue  # Try next model
                    
            except requests.exceptions.Timeout:
                brain_logger.warning(f"Timeout on {model} (attempt {attempt}/{len(models_to_try)})")
                log_ollama_error(f"Request timeout on {model}", url_base)
                continue
            except requests.exceptions.ConnectionError as e:
                brain_logger.error(f"Connection error with {model}: {str(e)}")
                log_ollama_error(f"Connection error: {str(e)}", url_base)
                continue
            except Exception as e:
                brain_logger.error(f"Unexpected error with {model}: {str(e)}")
                log_ollama_error(f"Unexpected error: {str(e)}", url_base)
                continue
        
        # All models failed
        brain_logger.error(f"❌ All models failed after {len(models_to_try)} attempts")
        return [{"speaker": "System", "text": f"All AI models failed. Check Ollama is running at {url_base}"}]
    else:
        # Cloud logic (same as before)
        pass