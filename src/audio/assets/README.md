# 🎺 Audio Assets

This folder contains production audio assets for RepoRadio.

## Contents

### Jingles
- `intro_jingle.mp3` - Opening podcast jingle (5-10 seconds)
- `outro_jingle.mp3` - Closing podcast jingle (5-10 seconds)
- `ad_transition.mp3` - Sound effect for sponsor break transitions (2-3 seconds)

### Sound Effects (Optional - Phase 2)
- `gavel.mp3` - Criticism/judgment sound (Sam, Marcus)
- `applause.mp3` - Celebration/excitement sound
- `alert.mp3` - Security warning sound (Marcus)
- `tech_whoosh.mp3` - Tech jargon emphasis

## Usage

These files are automatically loaded by the audio mixer when enabled in the UI:
- **Intro/Outro Jingles** - Toggle "🎺 Intro/Outro Jingles" in Settings
- **Ad Transitions** - Automatically used when "📢 Sponsor Breaks" is enabled
- **Sound Effects** - Context-aware (future feature)

## File Requirements

- **Format:** MP3 or WAV
- **Sample Rate:** 44.1kHz recommended
- **Channels:** Mono or Stereo
- **Bit Rate:** 128-320 kbps for MP3

## Fallback Behavior

If files are missing:
- Intro/outro: Podcast plays without jingles
- Ad transition: Uses 300ms silence instead
- Sound effects: No SFX added

---

**Note:** Add your own royalty-free jingles and sound effects here. The folder currently contains placeholders.
