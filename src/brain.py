import os
import json
import requests
import subprocess
from openai import OpenAI

SYSTEM_PROMPT = """
You are the producer of 'RepoRadio'.
Hosts:
- ALEX (The Hype Man): Enthusiastic, loves tech, uses slang like 'based', 'ship it'.
- SAM (The Senior Dev): Cynical, obsessed with testing and memory safety.
Format: Return ONLY a valid JSON list of objects: [{"speaker": "Alex", "text": "..."}]
"""

def get_host_ip():
    """Auto-detects the Host Machine IP from inside the container."""
    # Check for environment variable override first
    if os.getenv("OLLAMA_HOST"):
        return os.getenv("OLLAMA_HOST")
    
    try:
        # Check the default gateway
        cmd = "ip route show default | awk '{print $3}'"
        result = subprocess.check_output(cmd, shell=True).decode().strip()
        
        # Split by lines and take the first one
        # This handles cases where multiple gateways are returned
        first_ip = result.split('\n')[0].strip()
        
        return first_ip if first_ip else "127.0.0.1"
    except:
        # Fallback for local testing
        return "127.0.0.1"

def generate_script(repo_content, provider="Local (Ollama)"):
    print(f"🧠 Brain: Generating script using {provider}...")
    
    if "Local" in provider:
        # --- AUTO-DETECT IP ---
        host_ip = get_host_ip()
        url = f"http://{host_ip}:11434/api/generate"
        print(f"🔌 Connecting to Ollama at: {url}")

        try:
            # Use qwen3:30b which is available on the server
            prompt = f"{SYSTEM_PROMPT}\n\nAnalyze this repo:\n{repo_content}\n\nRespond with ONLY valid JSON."
            payload = {
                "model": "llama3.1:8b",
                "prompt": prompt,
                "stream": False
            }
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            # Extract the response text and parse JSON
            response_text = data.get("response", "")
            return json.loads(response_text)
        except Exception as e:
            return [{"speaker": "System", "text": f"Ollama Error ({url}): {str(e)}"}]

    else:
        # --- CLOUD (Siray / OpenAI) ---
        try:
            client = OpenAI(
                api_key=os.getenv("SIRAY_API_KEY") or os.getenv("OPENAI_API_KEY"),
                base_url="https://api.siray.ai/v1" if os.getenv("SIRAY_API_KEY") else None
            )
            completion = client.chat.completions.create(
                model="gpt-4o", 
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze this repo:\n{repo_content}"}
                ],
                response_format={ "type": "json_object" }
            )
            data = json.loads(completion.choices[0].message.content)
            return data.get("script", data)
        except Exception as e:
            return [{"speaker": "System", "text": f"Cloud API Error: {str(e)}"}]