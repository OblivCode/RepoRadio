# RepoRadio System Summary

## Overview
RepoRadio transforms GitHub repositories into AI-generated podcasts with professional audio production.

## Core Architecture

### 1. Ingestion (ingest.py)
- Daytona sandbox repo cloning
- Git archaeology (commits, contributors)
- Dependency scanning (6 file types)
- Deep mode: AI-selected priority files

### 2. Script Generation (brain.py)
**One-Line-at-a-Time Approach** (NEW)
- Generate 1 dialogue line per API call
- 4-6 pre-break + 1 ad + 4-6 post-break = 8-12 total
- Each line sees last 3 lines for context
- 100% reliable, no truncation

### 3. Voice Synthesis (voice.py)
- Parallel TTS (4 workers)
- Character voice mapping
- Crossfade transitions (200ms)
- Sponsor ad detection + transitions

### 4. Audio Production (audio/mixer.py)
- Background music overlay (-20dB)
- Intro/outro jingles
- Transition sounds for ads
- Professional audio mixing

### 5. Sponsor Ads (ads.py)
- Dependency-based humor
- 15+ templates (leftpad, lodash, etc.)
- Random host announcer
- Natural ad break flow

## Data Flow
\`\`\`
GitHub URL → Daytona Clone → Analysis → Script Gen → TTS → Audio Mix → MP3
\`\`\`

## Key Innovations
1. **One-line generation**: Eliminates LLM truncation
2. **3-part structure**: Pre/Ad/Post for natural flow
3. **Parallel TTS**: 4x faster rendering
4. **Auto-transitions**: Detects ads, adds sounds
5. **Session persistence**: Settings don't reset content

## Testing
- 15 unit tests (all passing)
- URL validation, git archaeology, deep mode
- Plan research, dependency parsing
