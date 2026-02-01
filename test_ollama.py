#!/usr/bin/env python3
"""
Diagnostic script to test Ollama connectivity and JSON response format.
Run this to verify Ollama is working before using RepoRadio.
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def get_host_ip():
    if os.getenv("OLLAMA_IP"):
        return os.getenv("OLLAMA_IP")
    return "192.168.1.119"

def test_ollama_connection():
    """Test basic Ollama connectivity."""
    host_ip = get_host_ip()
    url = f"http://{host_ip}:11434/api/generate"
    
    print("=" * 60)
    print("🔍 OLLAMA DIAGNOSTIC TEST")
    print("=" * 60)
    print(f"\n📍 Testing Ollama at: {url}")
    
    # Test 1: Basic connectivity
    print("\n[1/3] Testing connectivity...")
    try:
        test_payload = {
            "model": "llama3.1:8b",
            "prompt": "Say 'hello' in one word.",
            "stream": False
        }
        response = requests.post(url, json=test_payload, timeout=10)
        response.raise_for_status()
        print("✅ Ollama is reachable")
    except requests.exceptions.ConnectionError:
        print("❌ FAILED: Cannot connect to Ollama")
        print(f"   Make sure Ollama is running at {host_ip}:11434")
        print("   Try: ollama serve")
        return False
    except requests.exceptions.Timeout:
        print("❌ FAILED: Connection timeout")
        return False
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False
    
    # Test 2: JSON format response
    print("\n[2/3] Testing JSON format response...")
    try:
        json_payload = {
            "model": "llama3.1:8b",
            "prompt": "Return a JSON list with one item: the word 'test'. Format: [\"test\"]",
            "stream": False,
            "format": "json"
        }
        response = requests.post(url, json=json_payload, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        response_text = data.get("response", "").strip()
        
        if not response_text:
            print("❌ FAILED: Empty response from Ollama")
            print(f"   Full response: {data}")
            return False
        
        print(f"   Raw response: {response_text[:200]}")
        
        try:
            parsed = json.loads(response_text)
            print(f"✅ Valid JSON returned: {parsed}")
        except json.JSONDecodeError as e:
            print(f"❌ FAILED: Invalid JSON in response")
            print(f"   Error: {str(e)}")
            print(f"   Response: {response_text}")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False
    
    # Test 3: Script generation format
    print("\n[3/3] Testing podcast script format...")
    try:
        script_payload = {
            "model": "llama3.1:8b",
            "prompt": """Generate a 2-line podcast script in JSON format.
Format: [{"speaker": "Alex", "text": "Hello!"}, {"speaker": "Casey", "text": "Hi there!"}]
Respond with ONLY valid JSON.""",
            "stream": False,
            "format": "json"
        }
        response = requests.post(url, json=script_payload, timeout=20)
        response.raise_for_status()
        
        data = response.json()
        response_text = data.get("response", "").strip()
        
        if not response_text:
            print("❌ FAILED: Empty response")
            return False
        
        parsed = json.loads(response_text)
        
        if isinstance(parsed, list) and len(parsed) > 0:
            if all(isinstance(item, dict) and "speaker" in item and "text" in item for item in parsed):
                print(f"✅ Valid podcast script format: {len(parsed)} lines")
                print(f"   Example: {parsed[0]}")
            else:
                print("⚠️  WARNING: JSON is list but wrong format")
                print(f"   Got: {parsed}")
        else:
            print("⚠️  WARNING: JSON is not a list of script lines")
            print(f"   Got: {type(parsed)}")
            
    except json.JSONDecodeError as e:
        print(f"❌ FAILED: Invalid JSON")
        print(f"   Error: {str(e)}")
        print(f"   Response: {response_text[:200]}")
        return False
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED - Ollama is working correctly!")
    print("=" * 60)
    print("\n💡 If RepoRadio still fails, check:")
    print("   1. OLLAMA_IP in .env matches your Ollama host")
    print("   2. Model llama3.1:8b is installed: ollama list")
    print("   3. Firewall allows connections to port 11434")
    return True

if __name__ == "__main__":
    test_ollama_connection()
