# Add this to the top of your python files
from dotenv import load_dotenv
load_dotenv()

import os
from daytona_sdk import Daytona

# This runs INSIDE your main Daytona workspace.
# It uses the SDK to spawn ephemeral "Agent" sandboxes to read other repos.
def get_repo_content(repo_url, deep_mode=False, provider="Local (Ollama)"):
    print(f"🕵️  Agent: Analyzing {repo_url}...")
    
    # Initialize SDK
    daytona = Daytona()
    
    # Create an ephemeral sandbox for the target repo
    # We use the 'standard' image to ensure git/tools are present
    try:
        print("🚀 Agent: Spinning up isolated sandbox...")
        # Create an ephemeral sandbox for the target repo
        sandbox = daytona.create()
        
        # Clone the target repo inside that sandbox
        print(f"📦 Agent: Cloning {repo_url}...")
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        
        clone_res = sandbox.process.exec(f"git clone {repo_url}")
        if clone_res.exit_code != 0:
            return f"Error cloning: {clone_res.result}"
            
        # Read the README
        print("📖 Agent: Reading documentation...")
        read_res = sandbox.process.exec(f"cat {repo_name}/README.md")
        
        # Grab file structure (useful for the podcast hosts to discuss)
        tree_res = sandbox.process.exec(f"find {repo_name} -maxdepth 2 -not -path '*/.*'")
        
        # Cleanup (Kill the sandbox to save resources)
        print("💥 Agent: Job done. Destroying sandbox.")
        try:
            daytona.delete(sandbox)
        except:
            print("⚠️ Cleanup failed. You may need to manually delete this sandbox later.")
        
        full_report = f"README CONTENT:\n{read_res.result}\n\nFILE STRUCTURE:\n{tree_res.result}"
        return full_report

    except Exception as e:
        return f"Agent Error: {str(e)}"

# Quick test if you run this file directly
if __name__ == "__main__":
    print(get_repo_content("https://github.com/daytonaio/daytona"))