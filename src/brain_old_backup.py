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

Generate the next line of dialogue. Return ONLY JSON: {{\"speaker\": \"Name\", \"text\": \"...\"}}"""
            
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
                print(f"   \ud83c\udf99\ufe0f {line['speaker']}: {line['text'][:60]}...")
            else:
                brain_logger.warning(f"Failed to generate pre-break line {i+1}")
        
        # PART 2: Ad break (if enabled)
        if include_ad_break and dependencies:
            brain_logger.info("Inserting sponsor ad break")
            from ads import generate_fake_ad
            ad_line = generate_fake_ad(dependencies, host_names)
            if ad_line:
                script.append(ad_line)
                print(f"   \ud83d\udce2 {ad_line['speaker']}: {ad_line['text'][:60]}...")
        
        # PART 3: Post-break conversation
        brain_logger.info(f"Generating post-break conversation ({POST_BREAK_LINES} lines)")
        for i in range(POST_BREAK_LINES):
            line = generate_one_line(script, context_note="Dive deeper into technical details and wrap up.")
            if line:
                script.append(line)
                print(f"   \ud83c\udf99\ufe0f {line['speaker']}: {line['text'][:60]}...")
            else:
                brain_logger.warning(f"Failed to generate post-break line {i+1}")
        
        if not script:
            brain_logger.error("\u274c All one-line generations failed")
            return [{"speaker": "System", "text": f"Script generation failed. Check Ollama at {url_base}"}]
        
        brain_logger.info(f"\u2705 Successfully generated {len(script)} line script")
        return script
            """Return a list of {speaker,text} dicts or None."""
            script_list = None
            if isinstance(parsed_json, list):
                script_list = parsed_json
            elif isinstance(parsed_json, dict):
                # Check if it's a single script line (has speaker and text keys)
                if "speaker" in parsed_json and "text" in parsed_json:
                    brain_logger.debug("Received single script line, wrapping in list")
                    script_list = [parsed_json]
                else:
                    # Try common wrapper keys
                    for key in ["script", "podcast", "lines", "dialogue", "conversation"]:
                        if key in parsed_json and isinstance(parsed_json[key], list):
                            script_list = parsed_json[key]
                            brain_logger.debug(f"Extracted script from '{key}' wrapper")
                            break
            if not script_list:
                return None

            normalized = []
            for item in script_list:
                if not isinstance(item, dict):
                    continue
                speaker = item.get("speaker")
                text = item.get("text")
                if isinstance(speaker, str) and isinstance(text, str) and speaker.strip() and text.strip():
                    normalized.append({"speaker": speaker.strip(), "text": text.strip()})
            return normalized if normalized else None

        def _dedupe_keep_order(lines):
            seen = set()
            out = []
            for line in lines:
                key = (line.get("speaker"), line.get("text"))
                if key in seen:
                    continue
                seen.add(key)
                out.append(line)
            return out
        
        for attempt, model in enumerate(models_to_try, 1):
            try:
                # Truncate content for reliability (allow more with deep mode)
                max_chars = 3000 if "DEEP DIVE CODE" in repo_content else 2000
                content_preview = repo_content[:max_chars] if len(repo_content) > max_chars else repo_content
                
                # Build a more forceful prompt with repeat instructions
                full_prompt = f"""{system_prompt}

Repo Analysis:
{content_preview}

REMEMBER: You MUST generate a complete podcast with 8-12 conversation turns.
REMEMBER: Return a JSON array starting with [ and ending with ].
REMEMBER: Each turn needs speaker and text keys.

OUTPUT REQUIREMENTS (strict):
- Output MUST be a JSON array with between {MIN_TURNS} and {MAX_TURNS} items.
- Each item MUST be an object with exactly: speaker (string), text (string).
- Do NOT include any other keys.
- Do NOT wrap inside {{"script": ...}} or any wrapper.

Example format:
[
  {{"speaker": "Alex", "text": "..."}},
  {{"speaker": "Casey", "text": "..."}}
]

Generate the full 8-12 line podcast script now:"""

                def _ollama_generate(prompt_text, round_label, use_json_mode=True):
                    payload = {
                        "model": model,
                        "prompt": prompt_text,
                        "stream": False,
                        "options": {
                            "num_predict": 3000,
                            "temperature": 0.8,
                            "top_p": 0.9,
                            "repeat_penalty": 1.1,
                        },
                    }
                    if use_json_mode:
                        payload["format"] = "json"
                    brain_logger.debug(
                        f"Attempt {attempt}/{len(models_to_try)}: model={model} round={round_label}"
                    )
                    log_ollama_request(model, prompt_text, url_base)
                    start_time = time.time()
                    response = requests.post(url_base, json=payload, timeout=60)
                    response.raise_for_status()
                    data = response.json()
                    response_text = data.get("response", "").strip()
                    duration_ms = (time.time() - start_time) * 1000
                    if not response_text:
                        brain_logger.warning(f"Empty response from {model} at {url_base}")
                        brain_logger.debug(f"Full response object: {data}")
                        return None
                    log_ollama_response(response_text, duration_ms)

                    parsed = None
                    try:
                        parsed = json.loads(response_text)
                    except json.JSONDecodeError:
                        if not use_json_mode:
                            # Best-effort: extract JSON array/object from mixed text
                            start_candidates = [response_text.find("["), response_text.find("{")]
                            start_candidates = [i for i in start_candidates if i != -1]
                            if start_candidates:
                                start_idx = min(start_candidates)
                                end_idx = max(response_text.rfind("]"), response_text.rfind("}"))
                                if end_idx != -1 and end_idx > start_idx:
                                    candidate = response_text[start_idx : end_idx + 1]
                                    try:
                                        parsed = json.loads(candidate)
                                    except json.JSONDecodeError as e:
                                        brain_logger.warning(
                                            f"JSON parse error from {model} (substring): {str(e)}"
                                        )
                                        brain_logger.debug(f"Candidate: {candidate[:200]}")
                                        return None
                        if parsed is None:
                            brain_logger.warning(f"JSON parse error from {model} in round={round_label}")
                            brain_logger.debug(f"Response text: {response_text[:200]}")
                            return None
                    return _extract_script_list(parsed)

                all_lines = []
                first = _ollama_generate(full_prompt, "initial")
                if first:
                    all_lines.extend(first)
                    all_lines = _dedupe_keep_order(all_lines)

                # If the model stops early (common in JSON mode), ask it to continue.
                continuation_round = 0
                while len(all_lines) < MIN_TURNS and continuation_round < MAX_CONTINUATION_ROUNDS:
                    continuation_round += 1
                    brain_logger.info(
                        f"Script too short ({len(all_lines)}/{MIN_TURNS}); requesting continuation {continuation_round}/{MAX_CONTINUATION_ROUNDS}"
                    )
                    remaining_min = max(MIN_TURNS - len(all_lines), 1)
                    remaining_max = max(min(MAX_TURNS - len(all_lines), 6), remaining_min)

                    continue_prompt = f"""{system_prompt}

Repo Analysis:
{content_preview}

You already produced this partial script (JSON):
{json.dumps(all_lines, ensure_ascii=False)}

Continue the podcast.
STRICT OUTPUT: Return ONLY a JSON array of ADDITIONAL turns (no wrapper keys), do not repeat any existing turn.
Add {remaining_min} to {remaining_max} more turns so total becomes between {MIN_TURNS} and {MAX_TURNS} turns.
"""

                    more = _ollama_generate(continue_prompt, f"continue-{continuation_round}")
                    if not more:
                        brain_logger.warning(
                            f"Continuation round {continuation_round} produced no parsable turns"
                        )
                        continue
                    all_lines.extend(more)
                    all_lines = _dedupe_keep_order(all_lines)

                # Fallback: try once without Ollama JSON mode (it sometimes truncates early).
                if 0 < len(all_lines) < MIN_TURNS:
                    brain_logger.info(
                        "Still short after continuations; retrying once without JSON mode"
                    )
                    remaining_min = max(MIN_TURNS - len(all_lines), 1)
                    remaining_max = max(min(MAX_TURNS - len(all_lines), 8), remaining_min)
                    fallback_prompt = f"""{system_prompt}

Repo Analysis:
{content_preview}

You already produced this partial script (JSON):
{json.dumps(all_lines, ensure_ascii=False)}

Continue the podcast.
Return ONLY a JSON array of ADDITIONAL turns (no wrapper keys), do not repeat any existing turn.
Add {remaining_min} to {remaining_max} more turns so total becomes between {MIN_TURNS} and {MAX_TURNS} turns.
"""
                    more = _ollama_generate(fallback_prompt, "fallback-nonjson", use_json_mode=False)
                    if more:
                        all_lines.extend(more)
                        all_lines = _dedupe_keep_order(all_lines)

                if all_lines:
                    final_lines = all_lines[:MAX_TURNS]
                    if len(final_lines) < MIN_TURNS:
                        brain_logger.warning(
                            f"Generated only {len(final_lines)} turns (<{MIN_TURNS}) after continuations"
                        )
                    brain_logger.info(
                        f"✅ Successfully generated script with {model} ({len(final_lines)} lines)"
                    )
                    return final_lines

                brain_logger.warning(
                    f"Unexpected or empty response format from {model} (no turns extracted)"
                )
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