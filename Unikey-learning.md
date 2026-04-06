# Unikey Engine Analysis & Learning Plan

Findings from comparing x-unikey-1.0.4 (`src/ukengine/`) with MyVNKey's `telex_engine.py` + `vn_validator.py`.

## Index

1. [Auto-restore non-Vietnamese keystrokes](#1-auto-restore-non-vietnamese-keystrokes) — HIGH
2. [Keystroke buffer for undo/restore](#2-keystroke-buffer-for-undorestore) — HIGH
3. [Exhaustive vowel + final consonant pair table](#3-exhaustive-vowel--final-consonant-pair-table) — HIGH
4. [Full CVC triplet validation](#4-full-cvc-triplet-validation) — MEDIUM
5. [Modern vs traditional tone placement](#5-modern-vs-traditional-tone-placement) — MEDIUM
6. [Data-driven tone placement](#6-data-driven-tone-placement) — MEDIUM
7. [Free marking vs strict mode](#7-free-marking-vs-strict-mode) — LOW
8. [Backspace tone repositioning](#8-backspace-tone-repositioning) — MEDIUM
9. [Macro support](#9-macro-support) — LOW
10. [`gi` standalone tone handling](#10-gi-standalone-tone-handling) — MEDIUM

---

## 1. Auto-restore non-Vietnamese keystrokes

**Unikey**: At word boundary (space, punctuation), `processWordEnd()` calls `lastWordIsNonVn()`. If the completed word isn't a valid Vietnamese syllable, it calls `restoreKeyStrokes()` to undo all transforms and output the original ASCII keystrokes. Example: typing `dduowngf` then deciding mid-word it's not Vietnamese — at word break, Unikey reverts to the raw keys.

**MyVNKey**: Once a transform happens (e.g., `dd` → `đ`), it's permanent. Users typing mixed Vietnamese/English get stuck with unwanted diacritics.

**Source**: `ukengine.cpp:2235-2276` (`processWordEnd`), `ukengine.cpp:2282-2321` (`lastWordIsNonVn`), `ukengine.cpp:2143-2193` (`restoreKeyStrokes`).

**Implementation**: Check at word break whether the completed buffer forms a valid complete Vietnamese syllable. If not, replace the on-screen text with original raw keystrokes from the keystroke buffer.

---

## 2. Keystroke buffer for undo/restore

**Unikey**: Maintains a parallel `m_keyStrokes[MAX_UK_ENGINE]` array of `KeyBufEntry` structs, each recording the raw `UkKeyEvent` and a `converted` bool. This enables the restore feature — on restore, it replays the raw keystrokes through `processAppend()` (bypassing transform logic) to reconstruct the untransformed text.

**MyVNKey**: Only stores the transformed character buffer. No record of what the user actually typed.

**Source**: `ukengine.h:60-62` (struct), `ukengine.cpp:1785-1789` (recording), `ukengine.cpp:2143-2193` (restore replay).

**Implementation**: Add a parallel `raw_keystrokes` list in `KeyboardHandler` that records every typed character before transformation. Clear it on word break (after using it for restore check). This is a prerequisite for #1.

---

## 3. Exhaustive vowel + final consonant pair table

**Unikey**: Has an explicit `VCPairList[]` (~130 entries) enumerating every valid vowel-sequence + final-consonant combination, validated via binary search. For example, `ê` can end with `c, ch, m, n, nh, p, t` but NOT `ng`. The `isValidVC()` function first checks `conSuffix` (whether the vowel sequence allows any suffix at all) and `suffix` (whether the consonant can be a suffix), then checks the pair table.

**MyVNKey**: `vn_validator.py` only restricts `ch` and `nh` finals via `_FINAL_VOWEL_RESTRICT`. All other vowel+final combinations are implicitly allowed, so we accept impossible syllables like `ơng` (should be `ương` or `ông`).

**Source**: `ukengine.cpp:207-258` (VCPairList), `ukengine.cpp:367-387` (isValidVC).

**Implementation**: Port the VCPairList into a Python set of `(vowel_nucleus, final_consonant)` tuples and check against it in `vn_validator.is_valid_vietnamese()`.

---

## 4. Full CVC triplet validation

**Unikey**: `isValidCVC(c1, v, c2)` validates the entire initial+vowel+final as a unit, including exceptions:
- `qu` + `y` + `n/nh` → valid (quynh, quyn) despite `y+n` being invalid alone
- `gi` + `e/ê` + `n/ng` → valid (giêng) despite `e+ng` being invalid alone

**MyVNKey**: Validates C+V and V+C mostly independently, missing these cross-cutting exceptions.

**Source**: `ukengine.cpp:390-419` (`isValidCVC`).

---

## 5. Modern vs traditional tone placement

**Unikey**: `getTonePosition()` checks `m_pCtrl->options.modernStyle`. For diphthongs `oa`, `oe`, `uy`:
- Traditional: tone on first vowel → hòa, hòe, thùy
- Modern: tone on second vowel → hoà, hoè, thuỳ

**MyVNKey**: Always uses one style, no user option.

**Source**: `ukengine.cpp:929-951` (`getTonePosition`), `keycons.h:42` (`modernStyle` option).

---

## 6. Data-driven tone placement

**Unikey**: `getTonePosition()` uses structured `VowelSeqInfo` metadata:
1. If roofPos != -1 (â, ê, ô exists) → tone goes there
2. If hookPos != -1 (ơ, ư exists) → tone goes there (with ư+ơ special case)
3. If 3-vowel sequence → always position 1 (middle vowel)
4. Else: terminated ? position 0 : position 1

**MyVNKey**: `find_tone_target()` uses similar logic but ad-hoc. The modified-vowel priority and ươ/uô special cases are hardcoded.

**Source**: `ukengine.cpp:929-951`.

---

## 7. Free marking vs strict mode

**Unikey**: `freeMarking` option. In strict mode (`freeMarking=false`), diacritics can only modify the current cursor position. Check: `if (!freeMarking && changePos != m_current) return processAppend(ev)`. Appears in `processRoof`, `processHook`, `processDd`, `processTone`.

**MyVNKey**: Always allows free marking (reaching back into earlier vowels).

---

## 8. Backspace tone repositioning

**Unikey**: `processBackspace()` detects if deleting a character changes the required tone position and moves the tone mark. Example: deleting final `n` from `toán` should shift tone from `a` back to `o`.

**MyVNKey**: Backspace just pops the last character. No tone repositioning.

**Source**: `ukengine.cpp:1919-1976`.

---

## 9. Macro support

**Unikey**: Full macro table (`CMacroTable`) for text expansion. Type abbreviation + Enter → expands. Supports multi-word lookup at word boundaries.

**MyVNKey**: No macro system.

**Source**: `ukengine.cpp:2046-2140`, `mactab.cpp/h`.

---

## 10. `gi` standalone tone handling

**Unikey**: When the word form is `vnw_c` and the consonant is `cs_gi` or `cs_gin`, `processTone()` applies the tone directly to the `i` at the consonant position. This allows typing `gì`, `gí` correctly.

**MyVNKey**: `gi` is parsed as initial consonant in `vn_validator.py`, but tone application to the `i` within `gi` is not explicitly handled.

**Source**: `ukengine.cpp:954-974`.
