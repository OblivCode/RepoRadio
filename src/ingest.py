# Add this to the top of your python files
from dotenv import load_dotenv
load_dotenv()

import os
from daytona_sdk import Daytona
from debug_logger import ingest_logger, log_daytona_sandbox, log_daytona_error, log_git_clone

# This runs INSIDE your main Daytona workspace.
# It uses the SDK to spawn ephemeral "Agent" sandboxes to read other repos.
def get_repo_content(repo_url, deep_mode=False, provider="Local (Ollama)"):
    print(f"🕵️  Agent: Analyzing {repo_url}...")
    ingest_logger.info(f"Starting repo analysis: {repo_url}")
    
    # Initialize SDK
    daytona = Daytona()
    
    # Create an ephemeral sandbox for the target repo
    # We use the 'standard' image to ensure git/tools are present
    try:
        print("🚀 Agent: Spinning up isolated sandbox...")
        # Create an ephemeral sandbox for the target repo
        sandbox = daytona.create()
        ingest_logger.debug(f"Sandbox created: {sandbox.id}")
        log_daytona_sandbox("Sandbox created", sandbox.id)
        
        # Clone the target repo inside that sandbox
        print(f"📦 Agent: Cloning {repo_url}...")
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        ingest_logger.debug(f"Repository name: {repo_name}")
        
        clone_res = sandbox.process.exec(f"git clone {repo_url}")
        if clone_res.exit_code != 0:
            error_msg = f"Git clone failed: {clone_res.result}"
            ingest_logger.error(error_msg)
            log_git_clone(repo_url, False, clone_res.result)
            log_daytona_error(error_msg)
            return f"Error cloning: {clone_res.result}"
        
        ingest_logger.info(f"Successfully cloned {repo_url}")
        log_git_clone(repo_url, True)
            
        # Read the README
        print("📖 Agent: Reading documentation...")
        read_res = sandbox.process.exec(f"cat {repo_name}/README.md")
        ingest_logger.debug(f"README size: {len(read_res.result)} chars")
        
        # Grab file structure (useful for the podcast hosts to discuss)
        tree_res = sandbox.process.exec(f"find {repo_name} -maxdepth 2 -not -path '*/.*'")
        ingest_logger.debug(f"File tree size: {len(tree_res.result)} chars")
        
        # Cleanup (Kill the sandbox to save resources)
        print("💥 Agent: Job done. Destroying sandbox.")
        try:
            daytona.delete(sandbox)
            ingest_logger.debug(f"Sandbox deleted: {sandbox.id}")
            log_daytona_sandbox("Sandbox deleted", sandbox.id)
        except:
            ingest_logger.warning(f"Cleanup failed for sandbox {sandbox.id}")
            print("⚠️ Cleanup failed. You may need to manually delete this sandbox later.")
        
        full_report = f"README CONTENT:\n{read_res.result}\n\nFILE STRUCTURE:\n{tree_res.result}"
        ingest_logger.info(f"Repo analysis complete: {len(full_report)} chars total")
        return full_report

    except Exception as e:
        error_msg = f"Agent Error: {str(e)}"
        ingest_logger.error(error_msg)
        log_daytona_error(str(e))
        return error_msg

# Quick test if you run this file directly
if __name__ == "__main__":
    print(get_repo_content("https://github.com/daytonaio/daytona"))