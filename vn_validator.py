"""Vietnamese syllable structure validator.

Checks whether a character buffer could form a valid Vietnamese syllable
(or a valid prefix of one still being typed). Used to reject Telex
transformations that would produce impossible Vietnamese words.
"""

from telex_engine import ALL_VOWEL_CHARS, get_base_and_tone

# Valid Vietnamese initial consonants (lowercase)
VALID_INITIALS = {
    'b', 'c', 'ch', 'd', 'g', 'gh', 'gi', 'h', 'k', 'kh',
    'l', 'm', 'n', 'ng', 'ngh', 'nh', 'p', 'ph', 'q', 'r',
    's', 't', 'th', 'tr', 'v', 'x',
    'đ',
}

# Valid Vietnamese final consonants (lowercase)
VALID_FINALS = {
    'c', 'ch', 'm', 'n', 'ng', 'nh', 'p', 't',
}

# Maximum length of an initial or final consonant cluster
_MAX_INITIAL_LEN = 3  # "ngh"
_MAX_FINAL_LEN = 2    # "ch", "ng", "nh"


def _is_vowel_char(ch):
    """Check if ch is a Vietnamese vowel (any tone/case)."""
    return ch in ALL_VOWEL_CHARS


def _to_base_lower(ch):
    """Convert a (possibly toned) vowel to its base lowercase form.
    For consonants, just lowercase.
    """
    if ch in ALL_VOWEL_CHARS:
        info = get_base_and_tone(ch)
        if info:
            return info[0]  # base_lower
    return ch.lower()


def parse_syllable(buffer):
    """Parse a buffer (list of chars) into (initial, vowel, final) parts.

    Each part is a string of the raw characters from the buffer.
    Returns (initial_str, vowel_str, final_str) where any part can be empty.

    The parsing is greedy: it tries to match the longest valid initial
    consonant, then collects vowels, then collects final consonants.
    """
    if not buffer:
        return ('', '', '')

    chars = list(buffer)
    pos = 0
    n = len(chars)

    # --- Parse initial consonant (greedy, longest match) ---
    initial = ''
    best_initial_len = 0
    for length in range(1, min(_MAX_INITIAL_LEN, n) + 1):
        candidate = ''.join(_to_base_lower(c) for c in chars[:length])
        # Make sure these chars are all non-vowel (consonant-like)
        if any(_is_vowel_char(c) for c in chars[:length]):
            break
        if candidate in VALID_INITIALS:
            best_initial_len = length

    initial = ''.join(chars[:best_initial_len])
    pos = best_initial_len

    # Special case: if we couldn't match a valid initial but the leading
    # chars are consonants, they still form the "initial" (just invalid).
    if best_initial_len == 0:
        while pos < n and not _is_vowel_char(chars[pos]):
            pos += 1
        initial = ''.join(chars[:pos])

    # --- Parse vowel nucleus ---
    vowel_start = pos
    while pos < n and _is_vowel_char(chars[pos]):
        pos += 1
    vowel = ''.join(chars[vowel_start:pos])

    # --- Remainder is the final ---
    final = ''.join(chars[pos:])

    return (initial, vowel, final)


def is_valid_vietnamese(buffer):
    """Check if the buffer could be a valid Vietnamese syllable or a valid
    prefix of one still being typed.

    Returns True if the structure is consistent with Vietnamese phonology.
    Returns False if the structure is definitely not Vietnamese.
    """
    if not buffer:
        return True

    initial, vowel, final = parse_syllable(buffer)
    initial_lower = ''.join(_to_base_lower(c) for c in initial)
    final_lower = ''.join(_to_base_lower(c) for c in final)

    # Still typing the initial consonant - could be valid prefix
    if not vowel and not final:
        # Check if it's a valid initial or a prefix of one
        if initial_lower in VALID_INITIALS:
            return True
        # Check if it's a prefix of a valid initial (e.g., "n" could become "ng", "nh", "ngh")
        for vi in VALID_INITIALS:
            if vi.startswith(initial_lower):
                return True
        # Single consonant that isn't a valid initial (rare in Vietnamese)
        # Allow single chars as they could be start of typing
        if len(initial_lower) <= 1:
            return True
        return False

    # Has vowel but invalid initial consonant cluster
    if initial_lower and initial_lower not in VALID_INITIALS:
        # "đ" handling - check without tone marks
        if initial_lower != 'đ' and initial_lower not in VALID_INITIALS:
            return False

    # No final consonant yet - valid so far (still typing)
    if not final:
        return True

    # Has final consonant(s) - validate them
    if final_lower in VALID_FINALS:
        return True

    # Check if it's a prefix of a valid final (e.g., "n" could become "ng", "nh")
    for vf in VALID_FINALS:
        if vf.startswith(final_lower):
            return True

    return False
