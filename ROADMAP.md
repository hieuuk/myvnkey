# MyVNKey Roadmap

## Phase 1: Typing Accuracy Improvements

### 1.1 Enhanced Tone Placement
- [ ] Fix edge cases in 3+ vowel words (e.g., "khuya", "thuyen")
- [ ] Improve "qu" and "gi" vowel exclusion for uncommon words
- [ ] Add phonotactic constraints (forbidden consonant-vowel combos)

### 1.2 Smarter Syllable Validation
- [ ] Add valid vowel nucleus table (not all vowel combos are valid Vietnamese)
- [ ] Validate tone-final consonant compatibility (e.g., sắc/nặng only with -c/-ch/-p/-t finals)
- [ ] Reject invalid initial+vowel pairings (e.g., "kha" valid, "ka" not standard)

### 1.3 Retroactive Undo Improvements
- [ ] Support multi-step undo (currently only 1 transform deep)
- [ ] Better handling when user types English words that partially look Vietnamese

---

## Phase 2: New Features

### 2.1 VNI Input Method
- [ ] Add number-based tone input (1=sắc, 2=huyền, 3=hỏi, 4=ngã, 5=nặng, 6=circumflex, 7=horn, 8=breve, 9=đ, 0=remove)
- [ ] Allow switching between Telex/VNI in settings

### 2.2 Spell Check / Dictionary Integration
- [ ] Bundle a Vietnamese syllable dictionary (~7,000 valid syllables)
- [ ] Warn or auto-correct invalid but close syllables
- [ ] Optional "strict mode" that only allows dictionary words

### 2.3 Auto-Restore Clipboard
- [ ] Investigate SendInput timing for clipboard-based paste mode (faster than key-by-key)
- [ ] Fallback to keystroke mode when clipboard is unavailable

### 2.4 Macro / Text Expansion
- [ ] User-defined abbreviations (e.g., "addr" -> full address)
- [ ] Date/time insertion macros
- [ ] Configurable trigger key

### 2.5 Typing Statistics
- [ ] Track words typed per session
- [ ] Show Vietnamese vs English usage ratio
- [ ] Optional on-screen indicator overlay

---

## Phase 3: Polish & Distribution

### 3.1 Performance
- [ ] Cache compiled regex patterns in app_monitor
- [ ] Optimize vowel lookup with precomputed sets
- [ ] Profile and reduce latency in keystroke replacement

### 3.2 UI/UX
- [ ] Modernize settings GUI (consider web-based UI or Qt)
- [ ] Add tooltip showing current mode on tray hover
- [ ] Notification toast on mode switch (optional)
- [ ] Dark mode support for settings window

### 3.3 Packaging & Install
- [ ] PyInstaller single-exe build with CI
- [ ] MSI/NSIS installer with Start Menu shortcut
- [ ] Auto-update mechanism
- [ ] Code signing

### 3.4 Testing
- [ ] Unit tests for telex_engine (tone placement, transforms, undo)
- [ ] Unit tests for vn_validator (all valid/invalid syllable combos)
- [ ] Integration tests for keyboard_hook buffer management
- [ ] Automated regression suite for known edge cases

---

## Priorities

**High impact, do first:**
- Tone-final consonant validation (1.2) — prevents common wrong tones
- Valid vowel nucleus table (1.2) — catches gibberish syllables
- VNI input method (2.1) — many users prefer VNI over Telex
- Unit tests (3.4) — safety net for all future changes

**Medium impact:**
- Dictionary integration (2.2) — smarter suggestions
- Improved undo (1.3) — better English fallback
- Installer/packaging (3.3) — easier distribution

**Nice to have:**
- Macros (2.4), statistics (2.5), UI modernization (3.2)
