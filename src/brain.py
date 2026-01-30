import os
import json
import requests
import subprocess
from openai import OpenAI

# A generic base prompt. The {host_def} placeholders will be filled dynamically.
BASE_PROMPT = """
You are the producer of 'RepoRadio', a podcast discussing GitHub projects.
Your goal is to write a short, entertaining 3-minute banter script based on the provided code analysis.

The Hosts are:
{host1_def}
{host2_def}

Instructions:
- The hosts should banter back and forth, reacting to the provided "Repo Analysis".
- If "DEEP DIVE CODE" is present, have them quote specific lines.
- Keep it high energy and funny.

Format: Return ONLY a valid JSON list: [{{"speaker": "HostName", "text": "..."}}]
"""

def get_host_ip():
    # Check environment variables first (priority order)
    if os.getenv("OLLAMA_HOST"):
        return os.getenv("OLLAMA_HOST")
    if os.getenv("OLLAMA_IP"):
        return os.getenv("OLLAMA_IP")
    
    try:
        cmd = "ip route show default | awk '{print $3}'"
        result = subprocess.check_output(cmd, shell=True).decode().strip()
        return result.split('\n')[0].strip()
    except:
        return "127.0.0.1"

def load_character(char_name):
    """Reads the JSON file for a specific character."""
    try:
        # We assume the name matches the filename (e.g. "Alex" -> characters/alex.json)
        filename = f"characters/{char_name.lower()}.json"
        with open(filename, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Could not load character {char_name}: {e}")
        return {"name": char_name, "description": "A standard radio host."}

def generate_script(repo_content, host1, host2, provider="Local (Ollama)"):
    print(f"🧠 Brain: Generating script for {host1} vs {host2}...")
    
    # 1. Load the personality data
    h1_data = load_character(host1)
    h2_data = load_character(host2)
    
    # 2. Build the prompt dynamically
    h1_def = f"- {h1_data['name'].upper()}: {h1_data['description']}"
    h2_def = f"- {h2_data['name'].upper()}: {h2_data['description']}"
    
    system_prompt = BASE_PROMPT.format(host1_def=h1_def, host2_def=h2_def)
    
    # 3. Call the AI
    host_ip = get_host_ip()
    
    if "Local" in provider:
        url_base = f"http://{host_ip}:11434/api/generate"
        print(f"🔌 Connecting to Ollama at: {url_base}")
        
        try:
            # Build prompt for /api/generate endpoint
            prompt = f"{system_prompt}\n\nRepo Analysis:\n{repo_content}\n\nRespond with ONLY valid JSON."
            
            # Try models in order of availability
            models_to_try = ["llama3.1:8b", "qwen3:30b", "qwen3-coder:30b", "deepseek-r1:8b", "dolphin3:latest"]
            
            last_error = None
            for model in models_to_try:
                try:
                    print(f"  Trying model: {model}")
                    payload = {
                        "model": model,
                        "prompt": prompt,
                        "stream": False
                    }
                    response = requests.post(url_base, json=payload, timeout=120)
                    
                    if response.status_code == 404 and "model" in response.text.lower():
                        print(f"  Model {model} not found, trying next...")
                        continue
                    
                    response.raise_for_status()
                    data = response.json()
                    response_text = data.get("response", "")
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    print(f"  Failed to parse JSON from {model}")
                    last_error = f"Invalid JSON response from {model}"
                    continue
                except Exception as e:
                    print(f"  Error with {model}: {str(e)}")
                    last_error = str(e)
                    continue
            
            error_msg = last_error or "No models available"
            return [{"speaker": "System", "text": f"Ollama Error ({url_base}): {error_msg}"}]
            
        except Exception as e:
            return [{"speaker": "System", "text": f"Ollama Error ({url_base}): {str(e)}"}]
    else:
        # Cloud/OpenAI Logic
        try:
            client = OpenAI(
                api_key=os.getenv("SIRAY_API_KEY") or os.getenv("OPENAI_API_KEY"),
                base_url="https://api.siray.ai/v1" if os.getenv("SIRAY_API_KEY") else None
            )
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Repo Analysis:\n{repo_content}"}
                ],
                response_format={"type": "json_object"}
            )
            data = json.loads(completion.choices[0].message.content)
            return data.get("script", data)
        except Exception as e:
            return [{"speaker": "System", "text": f"Cloud Error: {str(e)}"}]