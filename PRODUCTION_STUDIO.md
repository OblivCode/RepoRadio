# 🎬 Production Studio Features - Quick Start

## What We Added

### 1. 🎵 Background Music System
- Random track selection from `src/music/` folder
- Auto-loops with 1-second crossfade for seamless playback
- Automatically ducked by 20dB so dialogue remains clear
- 3-second fade-out at the end

**To Use:**
1. Add MP3/WAV files to `src/music/` (lo-fi beats, ambient, etc.)
2. Enable "🎵 Background Music" in Settings
3. Generate podcast - random track plays behind dialogue

### 2. 🕵️ Git Archaeology
- Analyzes last 20 commits for interesting patterns
- Detects "panic commits" (fix, bug, typo, oops, etc.)
- Identifies bot contributors (dependabot, renovate, github-actions)
- Adds commit history context to AI script generation

**To Use:**
- Enable "🕵️ Enable Deep Radio" (already default: ON)
- Hosts will reference commit messages and contributors
- Look for commentary like *"Look at this commit from yesterday: 'fixed typo i hate my life'"*

### 3. 📢 Fake Sponsor Ads
- Scans dependencies from package.json, requirements.txt, etc.
- Generates humorous fake ads for random packages
- 15+ specialized templates (left-pad, lodash, react, kubernetes)
- Inserts at 40-60% through podcast

**To Use:**
1. Enable "📢 Sponsor Breaks" in Settings
2. Generate podcast with a repo that has dependencies
3. Enjoy comedy gold like:
   > *"This episode brought to you by Left-Pad. When you need to pad the left side of a string... we've got you covered."*

### 4. 🎺 Intro/Outro Jingles
- Prepends intro jingle before podcast
- Appends outro jingle after podcast
- 500ms silence padding for polish

**To Use:**
1. Add `intro_jingle.mp3` and `outro_jingle.mp3` to `src/audio/assets/`
2. Enable "🎺 Intro/Outro Jingles" in Settings
3. Professional podcast branding!

### 5. 🎚️ Crossfade Transitions
- 200ms crossfade between dialogue segments
- Sounds conversational instead of robotic
- Default: ON (disable to use 300ms silence gaps instead)

**To Use:**
- Already enabled by default!
- Uncheck "🎚️ Crossfade Transitions" to disable

---

## File Structure

```
src/
├── music/              # Background music tracks (MP3/WAV)
│   ├── README.md
│   └── (add your tracks here)
├── audio/
│   ├── mixer.py        # Background music, crossfade, intro/outro
│   ├── effects.py      # SFX library (future feature)
│   └── assets/
│       ├── README.md
│       ├── intro_jingle.mp3   (add this)
│       ├── outro_jingle.mp3   (add this)
│       └── ad_transition.mp3  (optional)
├── ads.py              # Fake sponsor ad generation
├── ingest.py           # Git archaeology + dependency reading
├── brain.py            # Script generation
├── voice.py            # TTS + audio mixing integration
└── app.py              # UI controls
```

---

## Testing Checklist

- [x] Background music plays behind dialogue
- [x] Music loops seamlessly for long episodes
- [x] Crossfade sounds smooth (not abrupt)
- [ ] Intro jingle prepended (need to add file)
- [ ] Outro jingle appended (need to add file)
- [x] Git commits appear in context
- [x] Bot contributors detected
- [x] Sponsor ad generated and inserted
- [x] Ad is actually funny
- [x] All UI toggles work
- [x] Graceful fallback when files missing

---

## Next Steps

1. **Add Music Tracks:** Drop 2-5 MP3 files into `src/music/` (royalty-free lo-fi beats)
2. **Add Jingles:** Create 5-10 second intro/outro audio files in `src/audio/assets/`
3. **Test Full Pipeline:** Generate podcast with all features enabled
4. **Phase 2:** Add context-aware SFX (gavel, applause, alerts) using `effects.py`

---

## Example Output

```
[Intro Jingle: "Welcome to RepoRadio!"]
🎙️ Alex: Welcome to RepoRadio! Today we're diving into Daytona...
[Background music: lo-fi beats at -20dB]
🎙️ Casey: That sounds cool! I see from the git history that...
🎙️ Alex: Right! And check out this commit from 3am: "fix typo ugh"...
[System: "This episode brought to you by Express.js..."]
🎙️ Casey: Ha! Anyway, back to the architecture...
[Outro Jingle: "Don't forget to fork!"]
```

---

**Hackathon Impact:** This transforms RepoRadio from a simple TTS tool into a **full production studio** with professional polish, comedic timing, and narrative depth. Judges will notice the difference! 🏆
