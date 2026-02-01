import os
import json
import requests
import subprocess
import time
import random
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
                
                # Try common wrapper keys first
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
                
                # If no wrapper found, treat dict keys as file paths (LLM explaining each file)
                if file_list is None:
                    # Extract keys where value indicates file exists
                    file_list = []
                    for filepath, status in parsed.items():
                        # Handle None or empty string - treat as valid file path
                        if status is None or status == "":
                            file_list.append(filepath)
                            brain_logger.debug(f"Extracted '{filepath}' from dict (status: {repr(status)})")
                            continue
                        
                        status_lower = str(status).lower()
                        # Include if status indicates file exists/is valid
                        if any(word in status_lower for word in ["found", "exists", "critical", "entry", "main"]):
                            file_list.append(filepath)
                            brain_logger.debug(f"Extracted '{filepath}' from dict (status: {status})")
                        elif "no such" in status_lower or "not found" in status_lower:
                            brain_logger.debug(f"Skipped '{filepath}' (status: {status})")
                    
                    if file_list:
                        brain_logger.info(f"Extracted {len(file_list)} files from explanatory dict")
            
            if file_list and len(file_list) > 0:
                brain_logger.info(f"Plan research identified {len(file_list)} files: {file_list}")
                return file_list[:3]  # Limit to 3 files max
            else:
                brain_logger.warning(f"Plan research returned unexpected format: {type(parsed)}, value: {parsed}")
                return []
                
        except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError, Exception) as e:
            brain_logger.error(f"Plan research failed: {str(e)}")
            return []
    else:
        return []

def generate_script(repo_content, host_names, provider="Local (Ollama)", include_ad_break=False, dependencies=""):
    """Generate podcast script for 1-3 hosts using one-line-at-a-time approach.
    
    New reliable approach: Generate one dialogue line at a time for 8-12 iterations.
    This avoids Ollama's JSON truncation issues with large outputs.
    
    Args:
        repo_content: Repository analysis text
        host_names: List of 1-3 character names
        provider: AI provider string
        include_ad_break: Whether to insert sponsor ad break
        dependencies: Dependency content for sponsor ad generation
    
    Returns:
        List of script objects with speaker and text fields (pre-break + ad + post-break)
    """
    hosts_str = ', '.join(host_names)
    print(f"🧠 Brain: Generating script for {hosts_str}...")
    brain_logger.info(f"Generating script for hosts: {hosts_str} | Provider: {provider} | Ad break: {include_ad_break}")
    
    # 1. Load Personality Data for all hosts
    host_characters = [load_character(name) for name in host_names]
    
    # 2. Build Prompt with dynamic host definitions
    host_defs = [f"- {h['name'].upper()}: {h['description']}" for h in host_characters]
    all_host_defs = "\n".join(host_defs)
    
    # Simple one-line prompt (no JSON array expectations)
    ONE_LINE_PROMPT = f"""You are producing RepoRadio, a podcast where tech experts discuss GitHub projects.

The Hosts:
{all_host_defs}

Your task: Generate ONE line of natural podcast dialogue.
- Make it conversational and engaging
- Explain technical concepts clearly
- Reference specific details from the repo analysis
- Stay in character

Return ONLY a JSON object with two fields:
{{"speaker": "HostName", "text": "What they say..."}}
"""
    
    host_ip = get_host_ip()
    
    if "Local" in provider:
        url_base = f"http://{host_ip}:11434/api/generate"
        model = "llama3.1:8b"
        
        # Generate 4-6 lines before ad, 4-6 after (8-12 total)
        PRE_BREAK_LINES = random.randint(4, 6)
        POST_BREAK_LINES = random.randint(4, 6)
        
        # Truncate content to avoid token limits
        max_chars = 2500
        content_preview = repo_content[:max_chars] if len(repo_content) > max_chars else repo_content
        
        def generate_one_line(conversation_so_far, context_note=""):
            """Generate a single dialogue line."""
            # Build context from previous lines
            prev_lines = "\n".join([f"{line['speaker']}: {line['text']}" for line in conversation_so_far[-3:]])  # Last 3 lines
            
            prompt = f"""{ONE_LINE_PROMPT}

Repo Analysis:
{content_preview}

{context_note}

Previous dialogue:
{prev_lines if prev_lines else "(This is the opening line)"}

Generate the next line of dialogue. Return ONLY JSON: {{"speaker": "Name", "text": "..."}}"""
            
            try:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "num_predict": 200,  # Short - one line only
                        "temperature": 0.9,
                        "top_p": 0.95,
                    }
                }
                
                brain_logger.debug(f"Requesting one line (conversation length: {len(conversation_so_far)})")
                response = requests.post(url_base, json=payload, timeout=30)
                response.raise_for_status()
                data = response.json()
                response_text = data.get("response", "").strip()
                
                if not response_text:
                    brain_logger.warning("Empty response for one-line generation")
                    return None
                
                parsed = json.loads(response_text)
                
                # Extract speaker and text
                speaker = parsed.get("speaker", "")
                text = parsed.get("text", "")
                
                if speaker and text:
                    return {"speaker": speaker.strip(), "text": text.strip()}
                else:
                    brain_logger.warning(f"Missing speaker or text in response: {parsed}")
                    return None
                    
            except Exception as e:
                brain_logger.warning(f"One-line generation error: {str(e)}")
                return None
        
        # PART 1: Pre-break conversation
        script = []
        brain_logger.info(f"Generating pre-break conversation ({PRE_BREAK_LINES} lines)")
        for i in range(PRE_BREAK_LINES):
            line = generate_one_line(script, context_note="Build excitement and introduce the project.")
            if line:
                script.append(line)
                print(f"   🎙️ {line['speaker']}: {line['text'][:60]}...")
            else:
                brain_logger.warning(f"Failed to generate pre-break line {i+1}")
        
        # PART 2: Ad break (if enabled)
        if include_ad_break and dependencies:
            brain_logger.info("Inserting sponsor ad break")
            from ads import generate_fake_ad
            ad_line = generate_fake_ad(dependencies, host_names)
            if ad_line:
                script.append(ad_line)
                print(f"   📢 {ad_line['speaker']}: {ad_line['text'][:60]}...")
        
        # PART 3: Post-break conversation
        brain_logger.info(f"Generating post-break conversation ({POST_BREAK_LINES} lines)")
        for i in range(POST_BREAK_LINES):
            # First line after ad should acknowledge the break
            if i == 0 and include_ad_break and dependencies:
                context_note = "We just came back from the sponsor break. Smoothly transition back to discussing the project. Maybe say something like 'Alright, back to the code!' or 'So where were we?' or just continue naturally."
            else:
                context_note = "Continue the technical discussion, dive deeper into implementation details, and build toward a conclusion."
            
            line = generate_one_line(script, context_note=context_note)
            if line:
                script.append(line)
                print(f"   🎙️ {line['speaker']}: {line['text'][:60]}...")
            else:
                brain_logger.warning(f"Failed to generate post-break line {i+1}")
        
        if not script:
            brain_logger.error("❌ All one-line generations failed")
            return [{"speaker": "System", "text": f"Script generation failed. Check Ollama at {url_base}"}]
        
        brain_logger.info(f"✅ Successfully generated {len(script)} line script")
        return script
    
    else:
        # Cloud logic (OpenAI/other providers)
        brain_logger.warning("Cloud providers not yet updated for new one-line approach")
        return [{"speaker": "System", "text": "Cloud provider script generation not implemented yet."}]
