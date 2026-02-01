# Add this to the top of your python files
from dotenv import load_dotenv
load_dotenv()

import os
import re
from daytona_sdk import Daytona
from brain import plan_research
from debug_logger import ingest_logger, log_daytona_sandbox, log_daytona_error, log_git_clone

def validate_github_url(url):
    """Validate and sanitize GitHub URL to prevent command injection."""
    # Strip whitespace first
    url = url.strip()
    
    # Basic GitHub URL pattern
    pattern = r'^https?://github\.com/[\w\-\.]+/[\w\-\.]+/?$'
    if not re.match(pattern, url.rstrip('.git')):
        raise ValueError(f"Invalid GitHub URL format: {url}")
    # Additional safety: ensure no shell metacharacters
    dangerous_chars = ['&', '|', ';', '$', '`', '\n', '(', ')']
    if any(char in url for char in dangerous_chars):
        raise ValueError(f"URL contains potentially dangerous characters: {url}")
    return url

# This runs INSIDE your main Daytona workspace.
# It uses the SDK to spawn ephemeral "Agent" sandboxes to read other repos.
def get_repo_content(repo_url, deep_mode=False, provider="Local (Ollama)"):
    print(f"🕵️  Agent: Analyzing {repo_url}...")
    ingest_logger.info(f"Starting repo analysis: {repo_url}")
    
    # Validate URL before using it
    try:
        repo_url = validate_github_url(repo_url)
    except ValueError as e:
        error_msg = f"URL validation failed: {str(e)}"
        ingest_logger.error(error_msg)
        return error_msg
    
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
        
        # Git Archaeology: Analyze repository history for drama/context
        git_history = ""
        dependencies_content = ""
        
        if deep_mode:
            print("🕵️ Agent: Analyzing git history...")
            ingest_logger.info("Git archaeology: extracting commit history and contributors")
            
            # Get recent commit messages (look for interesting patterns)
            git_log_res = sandbox.process.exec(f"git -C {repo_name} log --oneline -20 --date=short --format='%h|%ad|%s'")
            if git_log_res.exit_code == 0 and git_log_res.result:
                commits = git_log_res.result.strip().split('\n')
                ingest_logger.debug(f"Found {len(commits)} recent commits")
                
                # Analyze commits for interesting patterns
                late_night_commits = []
                panic_commits = []
                
                for commit in commits:
                    parts = commit.split('|')
                    if len(parts) >= 3:
                        commit_hash, date, message = parts[0], parts[1], '|'.join(parts[2:])
                        msg_lower = message.lower()
                        
                        # Detect panic/stress commits
                        if any(word in msg_lower for word in ['fix', 'bug', 'typo', 'oops', 'shit', 'fuck', 'damn', 'hate']):
                            panic_commits.append(f"{date}: {message}")
                        
                        # Store for general context
                        if len(late_night_commits) < 5:
                            late_night_commits.append(f"{date}: {message}")
                
                git_commits_summary = "\n".join(late_night_commits[:5])
                if panic_commits:
                    git_commits_summary += "\n\nINTERESTING COMMITS:\n" + "\n".join(panic_commits[:3])
                
                git_history += f"\n\nRECENT COMMITS:\n{git_commits_summary}"
                ingest_logger.debug(f"Collected {len(panic_commits)} interesting commits")
            
            # Get top contributors
            git_contrib_res = sandbox.process.exec(f"git -C {repo_name} shortlog -sn --all | head -10")
            if git_contrib_res.exit_code == 0 and git_contrib_res.result:
                contributors = git_contrib_res.result.strip()
                
                # Check for bots (dependabot, renovate, etc.)
                bot_contributors = []
                human_contributors = []
                for line in contributors.split('\n'):
                    if any(bot in line.lower() for bot in ['bot', 'dependabot', 'renovate', 'github-actions']):
                        bot_contributors.append(line)
                    else:
                        human_contributors.append(line)
                
                git_history += f"\n\nTOP CONTRIBUTORS:\n{contributors}"
                if bot_contributors:
                    git_history += f"\n\nBOT CONTRIBUTORS:\n" + "\n".join(bot_contributors)
                    ingest_logger.debug(f"Found {len(bot_contributors)} bot contributors")
                
                ingest_logger.info(f"Git archaeology complete: {len(git_history)} chars")
            
            # Read dependency files for sponsor ad generation
            print("📦 Agent: Scanning dependencies...")
            ingest_logger.info("Reading dependency files for sponsor content")
            
            deps_files = ["package.json", "requirements.txt", "Cargo.toml", "go.mod", "pom.xml", "composer.json"]
            for dep_file in deps_files:
                dep_res = sandbox.process.exec(f"cat {repo_name}/{dep_file} 2>/dev/null")
                if dep_res.exit_code == 0 and dep_res.result:
                    # Limit to first 1500 chars to avoid overwhelming context
                    content = dep_res.result[:1500] if len(dep_res.result) > 1500 else dep_res.result
                    dependencies_content = f"\n\nDEPENDENCIES ({dep_file}):\n{content}"
                    ingest_logger.info(f"Found dependencies in {dep_file}")
                    print(f"   📋 Found {dep_file}")
                    break  # Only need one dependency file
            
            if not dependencies_content:
                ingest_logger.debug("No dependency files found")

            
        # Read the README
        print("📖 Agent: Reading documentation...")
        read_res = sandbox.process.exec(f"cat {repo_name}/README.md")
        ingest_logger.debug(f"README size: {len(read_res.result)} chars")
        
        # Grab file structure (useful for the podcast hosts to discuss)
        tree_res = sandbox.process.exec(f"find {repo_name} -maxdepth 2 -not -path '*/.*'")
        ingest_logger.debug(f"File tree size: {len(tree_res.result)} chars")
        
        # Deep Radio Mode: Tool-calling style code analysis
        code_content = ""
        if deep_mode:
            print("🔍 Agent: Deep mode enabled - analyzing code files...")
            ingest_logger.info("Deep mode activated - using plan_research to identify key files")
            
            # Use AI to identify priority files (like tool calling for code agents)
            priority_files = plan_research(tree_res.result, provider)
            
            if priority_files and isinstance(priority_files, list):
                ingest_logger.info(f"Plan identified {len(priority_files)} priority files: {priority_files}")
                print(f"🎯 Agent: Reading {len(priority_files)} key files...")
                
                code_sections = []
                for filepath in priority_files:
                    # Read each priority file
                    file_res = sandbox.process.exec(f"cat {repo_name}/{filepath}")
                    
                    if file_res.exit_code == 0 and file_res.result:
                        file_size = len(file_res.result)
                        ingest_logger.debug(f"Read {filepath}: {file_size} chars")
                        print(f"   📄 {filepath} ({file_size} chars)")
                        
                        # Limit each file to prevent context overflow (max 2000 chars per file)
                        content = file_res.result[:2000] if len(file_res.result) > 2000 else file_res.result
                        code_sections.append(f"\n=== FILE: {filepath} ===\n{content}")
                    else:
                        ingest_logger.warning(f"Failed to read {filepath}: {file_res.result}")
                        print(f"   ⚠️ Could not read {filepath}")
                
                if code_sections:
                    code_content = "\n\nDEEP DIVE CODE:\n" + "\n".join(code_sections)
                    ingest_logger.info(f"Deep mode collected {len(code_content)} chars of code content")
            else:
                ingest_logger.warning("Plan research returned no files or invalid format")
                print("⚠️ Agent: Could not identify priority files for deep analysis")
        
        # Cleanup (Kill the sandbox to save resources)
        print("💥 Agent: Job done. Destroying sandbox.")
        try:
            daytona.delete(sandbox)
            ingest_logger.debug(f"Sandbox deleted: {sandbox.id}")
            log_daytona_sandbox("Sandbox deleted", sandbox.id)
        except:
            ingest_logger.warning(f"Cleanup failed for sandbox {sandbox.id}")
            print("⚠️ Cleanup failed. You may need to manually delete this sandbox later.")
        
        full_report = f"README CONTENT:\n{read_res.result}\n\nFILE STRUCTURE:\n{tree_res.result}{git_history}{dependencies_content}{code_content}"
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