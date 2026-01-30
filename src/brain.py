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
            data = json.load(f)
            log_character_load(char_name, True)
            return data
    except Exception as e:
        print(f"⚠️ Could not load character {char_name}: {e}")
        log_character_load(char_name, False, str(e))
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
    brain_logger.info(f"Generating script for hosts: {host1}, {host2} | Provider: {provider}")
    
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
        
        # Model fallback list for reliability
        models_to_try = ["llama3.1:8b", "llama2:13b", "neural-chat:7b"]
        
        for attempt, model in enumerate(models_to_try, 1):
            try:
                # Truncate content for reliability
                content_preview = repo_content[:1000] if len(repo_content) > 1000 else repo_content
                prompt = f"{system_prompt}\n\nRepo Analysis:\n{content_preview}\n\nRespond with ONLY valid JSON."
                
                payload = {"model": model, "prompt": prompt, "stream": False}
                
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
                
                # Validate it's a list of dictionaries
                if isinstance(parsed, list):
                    brain_logger.info(f"✅ Successfully generated script with {model}")
                    return parsed
                elif isinstance(parsed, dict) and "script" in parsed:
                    brain_logger.info(f"✅ Successfully generated script with {model}")
                    return parsed["script"]
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