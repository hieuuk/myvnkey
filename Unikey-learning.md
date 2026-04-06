# Unikey Engine Analysis & Learning Plan

Findings from comparing x-unikey-1.0.4 (`src/ukengine/`) with MyVNKey's `telex_engine.py` + `vn_validator.py`.

## Index

1. [Auto-restore non-Vietnamese keystrokes](#1-auto-restore-non-vietnamese-keystrokes) — HIGH — DONE
2. [Keystroke buffer for undo/restore](#2-keystroke-buffer-for-undorestore) — HIGH — DONE
3. [Exhaustive vowel + final consonant pair table](#3-exhaustive-vowel--final-consonant-pair-table) — HIGH — DONE
4. [Full CVC triplet validation](#4-full-cvc-triplet-validation) — MEDIUM — DONE
5. [Modern vs traditional tone placement](#5-modern-vs-traditional-tone-placement) — MEDIUM — DONE
6. [Data-driven tone placement](#6-data-driven-tone-placement) — MEDIUM — DONE
7. [Free marking vs strict mode](#7-free-marking-vs-strict-mode) — LOW
8. [Backspace tone repositioning](#8-backspace-tone-repositioning) — MEDIUM — DONE
9. [Macro support](#9-macro-support) — LOW
10. [`gi` standalone tone handling](#10-gi-standalone-tone-handling) — MEDIUM — DONE

---

## 1. Auto-restore non-Vietnamese keystrokes — DONE

**Unikey**: At word boundary (space, punctuation), `processWordEnd()` calls `lastWordIsNonVn()`. If the completed word isn't a valid Vietnamese syllable, it calls `restoreKeyStrokes()` to undo all transforms and output the original ASCII keystrokes. Example: typing `dduowngf` then deciding mid-word it's not Vietnamese — at word break, Unikey reverts to the raw keys.

**MyVNKey**: ~~Once a transform happens (e.g., `dd` → `đ`), it's permanent. Users typing mixed Vietnamese/English get stuck with unwanted diacritics.~~ Implemented in `keyboard_hook.py:_check_and_restore()`. At word boundaries (space, enter, tab, punctuation), checks `vn_validator.is_complete_vietnamese()` — if the word isn't valid Vietnamese but has transforms, restores original raw keystrokes.

**Source**: `ukengine.cpp:2235-2276` (`processWordEnd`), `ukengine.cpp:2282-2321` (`lastWordIsNonVn`), `ukengine.cpp:2143-2193` (`restoreKeyStrokes`).

---

## 2. Keystroke buffer for undo/restore — DONE

**Unikey**: Maintains a parallel `m_keyStrokes[MAX_UK_ENGINE]` array of `KeyBufEntry` structs, each recording the raw `UkKeyEvent` and a `converted` bool. This enables the restore feature — on restore, it replays the raw keystrokes through `processAppend()` (bypassing transform logic) to reconstruct the untransformed text.

**MyVNKey**: ~~Only stores the transformed character buffer. No record of what the user actually typed.~~ Implemented in `keyboard_hook.py` as `_raw_keystrokes` list + `_has_transforms` flag. Every character is recorded before transformation. Buffer history also saves/restores raw keystrokes across word boundaries.

**Source**: `ukengine.h:60-62` (struct), `ukengine.cpp:1785-1789` (recording), `ukengine.cpp:2143-2193` (restore replay).

---

## 3. Exhaustive vowel + final consonant pair table — DONE

**Unikey**: Has an explicit `VCPairList[]` (~130 entries) enumerating every valid vowel-sequence + final-consonant combination, validated via binary search. For example, `ê` can end with `c, ch, m, n, nh, p, t` but NOT `ng`. The `isValidVC()` function first checks `conSuffix` (whether the vowel sequence allows any suffix at all) and `suffix` (whether the consonant can be a suffix), then checks the pair table.

**MyVNKey**: ~~`vn_validator.py` only restricts `ch` and `nh` finals via `_FINAL_VOWEL_RESTRICT`. All other vowel+final combinations are implicitly allowed.~~ Implemented in `vn_validator.py` as `_VALID_VC_PAIRS` (139 valid pairs), `_NO_FINAL_NUCLEI` (29 nuclei that can't take finals), and `is_complete_vietnamese()` for strict end-of-word validation. Fuzzy matching preserved for in-progress typing.

**Source**: `ukengine.cpp:207-258` (VCPairList), `ukengine.cpp:367-387` (isValidVC).

---

## 4. Full CVC triplet validation — DONE

**Unikey**: `isValidCVC(c1, v, c2)` validates the entire initial+vowel+final as a unit, including exceptions:
- `qu` + `y` + `n/nh` → valid (quynh, quyn) despite `y+n` being invalid alone
- `gi` + `e/ê` + `n/ng` → valid (giêng) despite `e+ng` being invalid alone

**MyVNKey**: ~~Validates C+V and V+C mostly independently, missing these cross-cutting exceptions.~~ Implemented `_CVC_EXCEPTIONS` set in `vn_validator.py` with `(initial, nucleus, final)` triplets. Both `is_valid_vietnamese()` and `is_complete_vietnamese()` check exceptions before rejecting VC pairs.

**Source**: `ukengine.cpp:390-419` (`isValidCVC`).

---

## 5. Modern vs traditional tone placement — DONE

**Unikey**: `getTonePosition()` checks `m_pCtrl->options.modernStyle`. For diphthongs `oa`, `oe`, `uy`:
- Traditional: tone on first vowel → hòa, hòe, thùy
- Modern: tone on second vowel → hoà, hoè, thuỳ

**MyVNKey**: ~~Always uses one style, no user option.~~ Added `config.tone_style` setting (`'old'`/`'new'`). `find_tone_target()` in `telex_engine.py` checks this for `oa`, `oe`, `uy` diphthongs. Persisted in `~/.myvnkey.json`.

**Source**: `ukengine.cpp:929-951` (`getTonePosition`), `keycons.h:42` (`modernStyle` option).

---

## 6. Data-driven tone placement — DONE

**Unikey**: `getTonePosition()` uses structured `VowelSeqInfo` metadata:
1. If roofPos != -1 (â, ê, ô exists) → tone goes there
2. If hookPos != -1 (ơ, ư exists) → tone goes there (with ư+ơ special case)
3. If 3-vowel sequence → always position 1 (middle vowel)
4. Else: terminated ? position 0 : position 1

**MyVNKey**: ~~`find_tone_target()` uses similar logic but ad-hoc.~~ Improved in earlier commits: single modified vowel gets priority, ươ/uô diphthongs always place tone on second vowel, modern style support for oa/oe/uy added. Logic now closely follows Unikey's algorithm.

**Source**: `ukengine.cpp:929-951`.

---

## 7. Free marking vs strict mode

**Unikey**: `freeMarking` option. In strict mode (`freeMarking=false`), diacritics can only modify the current cursor position. Check: `if (!freeMarking && changePos != m_current) return processAppend(ev)`. Appears in `processRoof`, `processHook`, `processDd`, `processTone`.

**MyVNKey**: Always allows free marking (reaching back into earlier vowels).

---

## 8. Backspace tone repositioning — DONE

**Unikey**: `processBackspace()` detects if deleting a character changes the required tone position and moves the tone mark. Example: deleting final `n` from `toán` should shift tone from `a` back to `o`.

**MyVNKey**: ~~Backspace just pops the last character. No tone repositioning.~~ Implemented `_reposition_tone_after_delete()` in `keyboard_hook.py`. After deleting a character, it checks if the tone position needs to change via `find_tone_target()` and repositions by erasing and retyping the buffer.

**Source**: `ukengine.cpp:1919-1976`.

---

## 9. Macro support

**Unikey**: Full macro table (`CMacroTable`) for text expansion. Type abbreviation + Enter → expands. Supports multi-word lookup at word boundaries.

**MyVNKey**: No macro system.

**Source**: `ukengine.cpp:2046-2140`, `mactab.cpp/h`.

---

## 10. `gi` standalone tone handling — DONE

**Unikey**: When the word form is `vnw_c` and the consonant is `cs_gi` or `cs_gin`, `processTone()` applies the tone directly to the `i` at the consonant position. This allows typing `gì`, `gí` correctly.

**MyVNKey**: ~~`gi` is parsed as initial consonant in `vn_validator.py`, but tone application to the `i` within `gi` is not explicitly handled.~~ Added special case in `telex_engine.process_key()`: when buffer is exactly `['g', 'i']` and a tone key is pressed, tone is applied directly to the `i`. Handles all tones including undo.

**Source**: `ukengine.cpp:954-974`.
