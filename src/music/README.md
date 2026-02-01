# 🎵 Music & Audio Assets Folder

This folder contains organized audio assets for RepoRadio podcasts.

## Folder Structure

```
music/
├── intro.wav           # Podcast intro jingle (used automatically)
├── outro.wav           # Podcast outro jingle (used automatically)
├── background/         # Background music tracks (randomly selected)
│   ├── lofi-track-1.mp3
│   ├── lofi-track-2.mp3
│   └── ...
└── transitions/        # Ad break transition sounds (randomly selected)
    ├── transition1.wav
    ├── transition2.wav
    └── ...
```

## How It Works

### Intro & Outro
- `intro.wav` and `outro.wav` are **always used** when "🎺 Intro/Outro Jingles" is enabled
- Automatically prepended/appended to the podcast
- Keep these files 5-10 seconds long

### Background Music
- All files in `background/` folder are candidates for random selection
- One track is randomly chosen per podcast generation
- Volume automatically reduced by 20dB so dialogue remains clear
- Loops seamlessly if dialogue is longer than the music
- 3-second fade-out applied at the end

### Transitions
- All files in `transitions/` folder are used for ad break transitions
- One transition is randomly chosen when sponsor breaks are inserted
- Plays before and after the ad break
- Keep these files 2-3 seconds long

## Supported Formats

- `.mp3`
- `.wav`
- `.ogg`

## Track Requirements

**Intro/Outro:**
- Duration: 5-10 seconds
- Format: WAV recommended for quality
- Volume: Normal mastering levels

**Background Music:**
- Duration: 2-5 minutes (will loop for longer episodes)
- Genre: Lo-fi beats, ambient, chill electronic, tech news background music
- Volume: Normal mastering (auto-ducked by 20dB)

**Transitions:**
- Duration: 2-3 seconds
- Format: WAV recommended
- Style: Swoosh, whoosh, or subtle musical transition

## Usage

When production features are enabled:
1. **Background Music** - Random track from `background/` plays behind dialogue
2. **Intro/Outro** - `intro.wav` and `outro.wav` bookend the episode
3. **Transitions** - Random sound from `transitions/` used for ad breaks

All features are opt-in via the Settings expander in the UI.

---

**Note:** This folder is pre-populated with tracks. Organize them into subfolders as shown above.

