"""Core Telex transformation engine for Vietnamese Unicode typing."""

from __future__ import annotations

# Tone indices: 0=no tone, 1=sắc, 2=huyền, 3=hỏi, 4=ngã, 5=nặng
TONE_KEYS = {'s': 1, 'f': 2, 'r': 3, 'x': 4, 'j': 5, 'z': 0}

# Base vowels -> [no_tone, sắc, huyền, hỏi, ngã, nặng]
VOWEL_TABLE = {
    'a': ['a', 'á', 'à', 'ả', 'ã', 'ạ'],
    'ă': ['ă', 'ắ', 'ằ', 'ẳ', 'ẵ', 'ặ'],
    'â': ['â', 'ấ', 'ầ', 'ẩ', 'ẫ', 'ậ'],
    'e': ['e', 'é', 'è', 'ẻ', 'ẽ', 'ẹ'],
    'ê': ['ê', 'ế', 'ề', 'ể', 'ễ', 'ệ'],
    'i': ['i', 'í', 'ì', 'ỉ', 'ĩ', 'ị'],
    'o': ['o', 'ó', 'ò', 'ỏ', 'õ', 'ọ'],
    'ô': ['ô', 'ố', 'ồ', 'ổ', 'ỗ', 'ộ'],
    'ơ': ['ơ', 'ớ', 'ờ', 'ở', 'ỡ', 'ợ'],
    'u': ['u', 'ú', 'ù', 'ủ', 'ũ', 'ụ'],
    'ư': ['ư', 'ứ', 'ừ', 'ử', 'ữ', 'ự'],
    'y': ['y', 'ý', 'ỳ', 'ỷ', 'ỹ', 'ỵ'],
}

# Build uppercase table
VOWEL_TABLE_UPPER = {}
for base, variants in VOWEL_TABLE.items():
    VOWEL_TABLE_UPPER[base.upper()] = [v.upper() for v in variants]

# All vowel chars (all toned variants) -> (base, tone_index, is_upper)
CHAR_TO_BASE = {}
for base, variants in VOWEL_TABLE.items():
    for tone_idx, ch in enumerate(variants):
        CHAR_TO_BASE[ch] = (base, tone_idx)
for base, variants in VOWEL_TABLE_UPPER.items():
    for tone_idx, ch in enumerate(variants):
        CHAR_TO_BASE[ch] = (base, tone_idx)

# Set of all base vowels (lowercase)
BASE_VOWELS = set(VOWEL_TABLE.keys())
# Set of all vowel characters (any tone, any case)
ALL_VOWEL_CHARS = set(CHAR_TO_BASE.keys())

# Vowel transform rules: (preceding_base_lower, trigger_key_lower) -> new_base_lower
VOWEL_TRANSFORMS = {
    ('a', 'a'): 'â',
    ('a', 'w'): 'ă',
    ('e', 'e'): 'ê',
    ('o', 'o'): 'ô',
    ('o', 'w'): 'ơ',
    ('u', 'w'): 'ư',
}

# Undo transforms: typing the transform key again reverts
# e.g., â + a -> aa (undo), ă + w -> aw (undo)
VOWEL_UNDO = {
    ('â', 'a'): 'a',
    ('ă', 'w'): 'a',
    ('ê', 'e'): 'e',
    ('ô', 'o'): 'o',
    ('ơ', 'w'): 'o',
    ('ư', 'w'): 'u',
}

# Consonant transforms
CONSONANT_D_LOWER = 'đ'
CONSONANT_D_UPPER = 'Đ'


def is_vowel(ch):
    """Check if a character is a Vietnamese vowel (any tone, any case)."""
    return ch in ALL_VOWEL_CHARS


def get_base_and_tone(ch):
    """Get the base vowel and tone index for a Vietnamese vowel character.
    Returns (base_lower, tone_index, was_upper) or None if not a vowel.
    """
    if ch not in CHAR_TO_BASE:
        return None
    base, tone = CHAR_TO_BASE[ch]
    was_upper = ch.upper() == ch and ch.lower() != ch
    # Normalize base to lowercase
    base_lower = base.lower() if base.lower() in VOWEL_TABLE else base
    return (base_lower, tone, was_upper)


def apply_tone(base_lower, tone_idx, upper=False):
    """Return the vowel character with the given tone applied."""
    table = VOWEL_TABLE_UPPER if upper else VOWEL_TABLE
    base_key = base_lower.upper() if upper else base_lower
    if base_key in table:
        return table[base_key][tone_idx]
    return base_key


def find_tone_target(buffer):
    """Find the index in buffer where a tone mark should be placed.
    Implements Vietnamese tone placement rules.
    Returns index or -1 if no vowel found.
    """
    vowel_positions = []
    for i, ch in enumerate(buffer):
        if is_vowel(ch):
            vowel_positions.append(i)

    if not vowel_positions:
        return -1

    # Exclude 'u' in "qu" and 'i' in "gi" — these are part of the consonant
    if len(vowel_positions) >= 2:
        first_v = vowel_positions[0]
        if first_v >= 1:
            prev = buffer[first_v - 1].lower()
            first_base = get_base_and_tone(buffer[first_v])
            if first_base:
                fv_lower = first_base[0]
                if (prev == 'q' and fv_lower == 'u') or \
                   (prev == 'g' and fv_lower == 'i'):
                    vowel_positions = vowel_positions[1:]

    if not vowel_positions:
        return -1
    if len(vowel_positions) == 1:
        return vowel_positions[0]

    # Check for modified vowels (â, ă, ê, ô, ơ, ư) - these get priority
    for idx in vowel_positions:
        info = get_base_and_tone(buffer[idx])
        if info and info[0] in ('â', 'ă', 'ê', 'ô', 'ơ', 'ư'):
            return idx

    # Check if there's a consonant after the last vowel
    last_vowel_idx = vowel_positions[-1]
    has_trailing_consonant = False
    for i in range(last_vowel_idx + 1, len(buffer)):
        ch = buffer[i].lower()
        if ch not in ALL_VOWEL_CHARS and ch.isalpha():
            has_trailing_consonant = True
            break

    if has_trailing_consonant:
        # Tone on the last vowel before the final consonant
        return vowel_positions[-1]
    else:
        # No trailing consonant: tone on the penultimate vowel
        if len(vowel_positions) == 2:
            return vowel_positions[0]
        elif len(vowel_positions) >= 3:
            return vowel_positions[1]

    return vowel_positions[0]


def _find_vowel_for_transform(buffer, trigger_lower):
    """Find the rightmost vowel in buffer that can be transformed by the trigger key.
    Returns (index, base_lower, tone_idx, was_upper) or None.
    """
    for i in range(len(buffer) - 1, -1, -1):
        info = get_base_and_tone(buffer[i])
        if info is None:
            continue
        base_lower, tone_idx, was_upper = info
        if (base_lower, trigger_lower) in VOWEL_TRANSFORMS:
            return (i, base_lower, tone_idx, was_upper)
        # Check undo
        if (base_lower, trigger_lower) in VOWEL_UNDO:
            return (i, base_lower, tone_idx, was_upper)
    return None


def _validate_buffer(new_buffer):
    """Check if new_buffer is a valid Vietnamese syllable structure.
    Import here to avoid circular import at module level.
    """
    import vn_validator
    return vn_validator.is_valid_vietnamese(new_buffer)


def process_key(buffer, key):
    """Process a new key press against the current word buffer.

    Args:
        buffer: list of characters in the current word (already transformed)
        key: the new character typed (single char string)

    Returns:
        (new_buffer, backspace_count, transform_info): updated buffer, number
        of chars to delete before retyping, and transform info dict (or None).
        If backspace_count is 0, the key passes through normally (append only).

        transform_info (when not None) contains:
            'key': the literal key that triggered the transform
            'old_buffer': the buffer before this transform was applied
        This allows retroactive undo if subsequent characters invalidate
        the syllable.
    """
    key_lower = key.lower()
    key_upper = key.upper() == key and key.lower() != key

    # --- Handle tone keys ---
    if key_lower in TONE_KEYS and buffer:
        tone_idx = TONE_KEYS[key_lower]
        target = find_tone_target(buffer)
        if target >= 0:
            info = get_base_and_tone(buffer[target])
            if info:
                base_lower, current_tone, was_upper = info
                if tone_idx == 0:
                    # z = remove tone
                    if current_tone != 0:
                        new_char = apply_tone(base_lower, 0, was_upper)
                        new_buffer = buffer[:target] + [new_char] + buffer[target + 1:]
                        if _validate_buffer(new_buffer):
                            return (new_buffer, len(buffer), {'key': key, 'old_buffer': buffer[:]})
                    # No tone to remove, treat as regular char
                else:
                    if current_tone == tone_idx:
                        # Same tone again: remove it and output the key as literal
                        new_char = apply_tone(base_lower, 0, was_upper)
                        new_buffer = buffer[:target] + [new_char] + buffer[target + 1:] + [key]
                        return (new_buffer, len(buffer), None)
                    else:
                        new_char = apply_tone(base_lower, tone_idx, was_upper)
                        new_buffer = buffer[:target] + [new_char] + buffer[target + 1:]
                        if _validate_buffer(new_buffer):
                            return (new_buffer, len(buffer), {'key': key, 'old_buffer': buffer[:]})

    # --- Handle 'dd' -> đ ---
    if key_lower == 'd' and buffer:
        last = buffer[-1]
        if last == 'd':
            new_buffer = buffer[:-1] + [CONSONANT_D_LOWER]
            return (new_buffer, 1, {'key': key, 'old_buffer': buffer[:]})
        elif last == 'D':
            new_buffer = buffer[:-1] + [CONSONANT_D_UPPER]
            return (new_buffer, 1, {'key': key, 'old_buffer': buffer[:]})
        # Undo: đ + d -> dd
        elif last == CONSONANT_D_LOWER:
            new_buffer = buffer[:-1] + ['d', key]
            return (new_buffer, 1, None)
        elif last == CONSONANT_D_UPPER:
            new_buffer = buffer[:-1] + ['D', key.upper() if key_upper else key]
            return (new_buffer, 1, None)
        # Flexible dd: initial 'd' + vowels + 'd' -> 'đ' + vowels
        # e.g., "dod" -> "đo", "dươngd" -> "đương"
        elif buffer[0].lower() == 'd' and buffer[0] not in (CONSONANT_D_LOWER, CONSONANT_D_UPPER):
            # Check there's at least one vowel between the initial d and this d
            has_vowel = any(is_vowel(ch) for ch in buffer[1:])
            if has_vowel:
                new_d = CONSONANT_D_UPPER if buffer[0].isupper() else CONSONANT_D_LOWER
                new_buffer = [new_d] + buffer[1:]
                return (new_buffer, len(buffer), {'key': key, 'old_buffer': buffer[:]})

    # --- Handle vowel transforms (aa->â, aw->ă, ee->ê, oo->ô, ow->ơ, uw->ư) ---
    if key_lower in ('a', 'e', 'o', 'w'):
        result = _find_vowel_for_transform(buffer, key_lower)
        if result:
            idx, base_lower, tone_idx, was_upper = result

            # Check for undo first
            if (base_lower, key_lower) in VOWEL_UNDO:
                original_base = VOWEL_UNDO[(base_lower, key_lower)]
                new_char = apply_tone(original_base, tone_idx, was_upper)
                new_buffer = buffer[:idx] + [new_char] + buffer[idx + 1:] + [key]
                return (new_buffer, len(buffer) - idx, None)

            # Apply transform
            if (base_lower, key_lower) in VOWEL_TRANSFORMS:
                new_base = VOWEL_TRANSFORMS[(base_lower, key_lower)]
                new_char = apply_tone(new_base, tone_idx, was_upper)
                new_buffer = buffer[:idx] + [new_char] + buffer[idx + 1:]
                if _validate_buffer(new_buffer):
                    return (new_buffer, len(buffer) - idx, {'key': key, 'old_buffer': buffer[:]})

    # --- Handle 'w' transforming u->ư or o->ơ anywhere in the word ---
    if key_lower == 'w' and buffer:
        # Look for the rightmost u or o that can be transformed
        for i in range(len(buffer) - 1, -1, -1):
            info = get_base_and_tone(buffer[i])
            if info:
                base_lower, tone_idx, was_upper = info
                if (base_lower, 'w') in VOWEL_TRANSFORMS:
                    new_base = VOWEL_TRANSFORMS[(base_lower, 'w')]
                    new_char = apply_tone(new_base, tone_idx, was_upper)
                    new_buffer = buffer[:i] + [new_char] + buffer[i + 1:]
                    if _validate_buffer(new_buffer):
                        return (new_buffer, len(buffer) - i, {'key': key, 'old_buffer': buffer[:]})

    # --- No transformation: just append ---
    new_buffer = buffer + [key]
    return (new_buffer, 0, None)
