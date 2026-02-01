"""
Fake sponsor ad generation for RepoRadio.
Creates humorous sponsor breaks based on project dependencies.
"""
import random
import re
import json
from debug_logger import brain_logger


# Ad templates by package type
AD_TEMPLATES = {
    "generic": [
        "This episode is brought to you by {package}. When you absolutely, positively need to {action}, accept no substitutes.",
        "{package}: Because sometimes, you just need to {action}. Get started today at... well, you know where it is.",
        "Sponsored by {package}. Making {action} so easy, even your PM could do it. Probably.",
        "{package}: The dependency you didn't know you needed, until you really needed it.",
        "Today's episode brought to you by {package}. {tagline}",
    ],
    "leftpad": [
        "This episode is brought to you by Left-Pad. When you need to pad the left side of a string... we've got you covered. Literally.",
        "Left-Pad: Because sometimes, 11 lines of code can break the entire internet. Use responsibly.",
    ],
    "lodash": [
        "Lodash: Because native JavaScript array methods are overrated. Why use .map() when you can import an entire library?",
        "This episode sponsored by Lodash. Making JavaScript developers feel productive since 2012.",
    ],
    "react": [
        "React: Where every button needs its own component, every state change triggers a re-render, and your bundle size is... let's not talk about it.",
        "Brought to you by React. Because writing HTML in JavaScript seemed like a good idea at the time.",
    ],
    "kubernetes": [
        "Kubernetes: Because running one container was too simple. Now you need three operators, five CRDs, and a PhD.",
        "This episode sponsored by Kubernetes. Making simple problems complicated since 2014.",
    ],
    "axios": [
        "Axios: Because fetch() wasn't quite good enough. Add 10KB to your bundle for... better defaults?",
        "Brought to you by Axios. The HTTP client that does what fetch does, but with more ceremony.",
    ],
    "django": [
        "Django: The web framework with more built-in features than you'll ever use, but you'll install them all anyway.",
        "Sponsored by Django. Batteries included, assembly required.",
    ],
    "spring": [
        "Spring Framework: Where every application needs at least 47 annotations to say 'Hello World'.",
        "This episode brought to you by Spring. Because Java wasn't verbose enough already.",
    ],
}


def extract_dependencies(dependencies_content):
    """
    Extract package names from dependency file content.
    
    Args:
        dependencies_content: Raw content from package.json, requirements.txt, etc.
    
    Returns:
        List of package names
    """
    if not dependencies_content:
        return []
    
    packages = []
    
    try:
        # Try JSON (package.json, composer.json)
        if "{" in dependencies_content and "}" in dependencies_content:
            data = json.loads(dependencies_content)
            
            # package.json structure
            if "dependencies" in data:
                packages.extend(data["dependencies"].keys())
            if "devDependencies" in data:
                packages.extend(data["devDependencies"].keys())
        
        # Try plain text (requirements.txt, go.mod)
        else:
            lines = dependencies_content.split('\n')
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Extract package name (before version specifier)
                match = re.match(r'^([a-zA-Z0-9_-]+)', line)
                if match:
                    packages.append(match.group(1))
    
    except Exception as e:
        brain_logger.warning(f"Failed to parse dependencies: {str(e)}")
    
    return packages[:20]  # Limit to first 20


def generate_fake_ad(dependencies_content, host_names=None):
    """
    Generate a humorous fake sponsor ad based on project dependencies.
    
    Args:
        dependencies_content: String containing dependency file content
        host_names: List of host names (random one will announce the ad)
    
    Returns:
        Dict with speaker and text for ad break
    """
    packages = extract_dependencies(dependencies_content)
    
    # Select a random host to announce the ad, fallback to "Alex" or "System"
    if host_names and len(host_names) > 0:
        ad_speaker = random.choice(host_names)
    else:
        ad_speaker = "Alex"  # Default fallback
    
    if not packages:
        brain_logger.debug("No dependencies found, using generic ad")
        return {
            "speaker": ad_speaker,
            "text": "This episode is brought to you by Open Source Software. Free as in freedom, expensive as in maintenance. Support your local maintainer.",
            "type": "ad"
        }
    
    # Pick a random package
    package = random.choice(packages)
    package_lower = package.lower()
    
    brain_logger.info(f"Generating fake ad for package: {package}")
    
    # Check for special templates
    template_key = None
    for key in AD_TEMPLATES.keys():
        if key != "generic" and key in package_lower:
            template_key = key
            break
    
    # Select template
    if template_key:
        template = random.choice(AD_TEMPLATES[template_key])
    else:
        template = random.choice(AD_TEMPLATES["generic"])
    
    # Generate action/tagline if template needs it
    actions = [
        "manipulate arrays",
        "handle HTTP requests",
        "parse JSON",
        "validate forms",
        "manage state",
        "authenticate users",
        "transform data",
        "schedule tasks",
        "cache responses",
        "render templates",
    ]
    
    taglines = [
        "It's in your package.json. You don't remember adding it. But here we are.",
        "Downloaded 50 million times last week. Most of those were bots.",
        "Maintained by one person. Send coffee.",
        "Now with 100% more TypeScript types! (That nobody reads.)",
        "Because reinventing the wheel is so 2020.",
    ]
    
    # Format the ad
    ad_text = template.format(
        package=package,
        action=random.choice(actions),
        tagline=random.choice(taglines)
    )
    
    brain_logger.debug(f"Generated ad text: {ad_text[:100]}...")
    
    return {
        "speaker": ad_speaker,
        "text": ad_text,
        "type": "ad"
    }


def inject_ad_break(script, dependencies_content, host_names=None):
    """
    Inject a fake sponsor ad break into the middle of the script.
    
    Args:
        script: List of script line dicts
        dependencies_content: Dependency file content for ad generation
        host_names: List of host names (one will announce the ad)
    
    Returns:
        Modified script with ad break inserted
    """
    if len(script) < 6:
        brain_logger.warning("Script too short for ad break insertion")
        return script
    
    # Generate the ad with host announcement
    ad_break = generate_fake_ad(dependencies_content, host_names)
    
    # Insert at roughly the midpoint (between 40-60% through)
    total_lines = len(script)
    insert_position = int(total_lines * random.uniform(0.4, 0.6))
    
    # Insert ad break
    script.insert(insert_position, ad_break)
    brain_logger.info(f"Inserted ad break at position {insert_position}/{total_lines}")
    
    return script
