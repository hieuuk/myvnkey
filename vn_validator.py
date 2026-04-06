"""Vietnamese syllable structure validator.

Checks whether a character buffer could form a valid Vietnamese syllable
(or a valid prefix of one still being typed). Used to reject Telex
transformations that would produce impossible Vietnamese words.
"""

from telex_engine import ALL_VOWEL_CHARS, get_base_and_tone

# Valid Vietnamese initial consonants (lowercase)
VALID_INITIALS = {
    'b', 'c', 'ch', 'd', 'g', 'gh', 'gi', 'h', 'k', 'kh',
    'l', 'm', 'n', 'ng', 'ngh', 'nh', 'p', 'ph', 'q', 'qu', 'r',
    's', 't', 'th', 'tr', 'v', 'x',
    'đ',
}

# Valid Vietnamese final consonants (lowercase)
VALID_FINALS = {
    'c', 'ch', 'm', 'n', 'ng', 'nh', 'p', 't',
}

# Checked finals: syllables ending in these can ONLY have sắc (1) or nặng (5)
_CHECKED_FINALS = {'c', 'ch', 'p', 't'}

# Valid vowel nuclei (base lowercase forms, 1-3 vowels)
# Single vowels are always valid; this covers diphthongs and triphthongs.
_VALID_VOWEL_NUCLEI = {
    # Single vowels (all valid)
    'a', 'ă', 'â', 'e', 'ê', 'i', 'o', 'ô', 'ơ', 'u', 'ư', 'y',
    # Diphthongs
    'ai', 'ao', 'au', 'ay', 'âu', 'ây',
    'eo', 'êu',
    'ia', 'iê', 'iu',
    'oa', 'oă', 'oe', 'oi', 'oo', 'ôi',
    'ơi',
    'ua', 'uâ', 'uê', 'ui', 'uô', 'uơ', 'uy', 'uă',
    'ưa', 'ươ', 'ưi', 'ưu',
    'ya', 'yê',
    # Triphthongs
    'iêu', 'oai', 'oay', 'oeo',
    'uây', 'uôi', 'ươi', 'ươu',
    'uya', 'uyê', 'uyu',
    'yêu',
}

# Initial consonant -> allowed leading vowels for the nucleus.
# The check matches the FIRST base vowel of the nucleus, not the full nucleus.
# Initials not listed here can pair with any vowel.
_INITIAL_LEADING_VOWEL = {
    'k':   {'i', 'e', 'ê', 'y'},
    'gh':  {'i', 'e', 'ê'},
    'ngh': {'i', 'e', 'ê'},
    # 'q' is not restricted here because parse_syllable now absorbs 'qu' as
    # the initial when followed by a vowel, so the nucleus won't start with 'u'.
}

# Exhaustive set of valid (vowel_nucleus_base, final_consonant) pairs.
# Ported from Unikey's VCPairList in ukengine.cpp (~130 valid pairs).
# If a nucleus+final combination is not in this set, it's not a valid Vietnamese syllable.
_VALID_VC_PAIRS = {
    # a: c, ch, m, n, ng, nh, p, t
    ('a', 'c'), ('a', 'ch'), ('a', 'm'), ('a', 'n'), ('a', 'ng'), ('a', 'nh'), ('a', 'p'), ('a', 't'),
    # â: c, m, n, ng, p, t
    ('â', 'c'), ('â', 'm'), ('â', 'n'), ('â', 'ng'), ('â', 'p'), ('â', 't'),
    # ă: c, m, n, ng, p, t
    ('ă', 'c'), ('ă', 'm'), ('ă', 'n'), ('ă', 'ng'), ('ă', 'p'), ('ă', 't'),
    # e: c, ch, m, n, ng, nh, p, t
    ('e', 'c'), ('e', 'ch'), ('e', 'm'), ('e', 'n'), ('e', 'ng'), ('e', 'nh'), ('e', 'p'), ('e', 't'),
    # ê: c, ch, m, n, nh, p, t  (no "ng")
    ('ê', 'c'), ('ê', 'ch'), ('ê', 'm'), ('ê', 'n'), ('ê', 'nh'), ('ê', 'p'), ('ê', 't'),
    # i: c, ch, m, n, nh, p, t
    ('i', 'c'), ('i', 'ch'), ('i', 'm'), ('i', 'n'), ('i', 'nh'), ('i', 'p'), ('i', 't'),
    # o: c, m, n, ng, p, t
    ('o', 'c'), ('o', 'm'), ('o', 'n'), ('o', 'ng'), ('o', 'p'), ('o', 't'),
    # ô: c, m, n, ng, p, t
    ('ô', 'c'), ('ô', 'm'), ('ô', 'n'), ('ô', 'ng'), ('ô', 'p'), ('ô', 't'),
    # ơ: m, n, p, t  (no c, ng)
    ('ơ', 'm'), ('ơ', 'n'), ('ơ', 'p'), ('ơ', 't'),
    # u: c, m, n, ng, p, t
    ('u', 'c'), ('u', 'm'), ('u', 'n'), ('u', 'ng'), ('u', 'p'), ('u', 't'),
    # ư: c, m, n, ng, t  (no p)
    ('ư', 'c'), ('ư', 'm'), ('ư', 'n'), ('ư', 'ng'), ('ư', 't'),
    # y: t only
    ('y', 't'),
    # oo: ng, c  (xoong, soóc)
    ('oo', 'ng'), ('oo', 'c'),
    # iê (ie/iê): c, m, n, ng, p, t
    ('iê', 'c'), ('iê', 'm'), ('iê', 'n'), ('iê', 'ng'), ('iê', 'p'), ('iê', 't'),
    # oa: c, ch, m, n, ng, nh, p, t
    ('oa', 'c'), ('oa', 'ch'), ('oa', 'm'), ('oa', 'n'), ('oa', 'ng'), ('oa', 'nh'), ('oa', 'p'), ('oa', 't'),
    # oă: c, m, n, ng, t
    ('oă', 'c'), ('oă', 'm'), ('oă', 'n'), ('oă', 'ng'), ('oă', 't'),
    # oe: n, t
    ('oe', 'n'), ('oe', 't'),
    # ua: n, ng, t
    ('ua', 'n'), ('ua', 'ng'), ('ua', 't'),
    # uâ: n, ng, t
    ('uâ', 'n'), ('uâ', 'ng'), ('uâ', 't'),
    # uê: c, ch, n, nh
    ('uê', 'c'), ('uê', 'ch'), ('uê', 'n'), ('uê', 'nh'),
    # uô: c, m, n, ng, p, t
    ('uô', 'c'), ('uô', 'm'), ('uô', 'n'), ('uô', 'ng'), ('uô', 'p'), ('uô', 't'),
    # ươ: c, m, n, ng, p, t
    ('ươ', 'c'), ('ươ', 'm'), ('ươ', 'n'), ('ươ', 'ng'), ('ươ', 'p'), ('ươ', 't'),
    # uơ (alternate representation of ươ): c, m, n, ng, p, t
    ('uơ', 'c'), ('uơ', 'm'), ('uơ', 'n'), ('uơ', 'ng'), ('uơ', 'p'), ('uơ', 't'),
    # uy: c, ch, n, nh, p, t
    ('uy', 'c'), ('uy', 'ch'), ('uy', 'n'), ('uy', 'nh'), ('uy', 'p'), ('uy', 't'),
    # yê (ye/yê): m, n, ng, p, t  (no "c")
    ('yê', 'm'), ('yê', 'n'), ('yê', 'ng'), ('yê', 'p'), ('yê', 't'),
    # uyê: n, t
    ('uyê', 'n'), ('uyê', 't'),
    # uă: c, m, n, ng, t  (same pattern as oă, e.g. "quăng")
    ('uă', 'c'), ('uă', 'm'), ('uă', 'n'), ('uă', 'ng'), ('uă', 't'),
}

# Vowel nuclei that CANNOT take any final consonant at all.
# If the nucleus is one of these and a valid final consonant follows, reject.
_NO_FINAL_NUCLEI = {
    # Diphthongs with no final
    'ai', 'ao', 'au', 'ay', 'âu', 'ây',
    'eo', 'êu',
    'ia', 'iu',
    'oi', 'ôi', 'ơi',
    'ui',
    'ưa', 'ưi', 'ưu',
    'ya',
    # Triphthongs with no final
    'iêu', 'oai', 'oay', 'oeo',
    'uây', 'uôi', 'ươi', 'ươu',
    'uya', 'uyu', 'yêu',
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

    # Special case: "gi" and "qu" are initials that contain vowel chars.
    # "gi" is an initial when followed by another vowel (gia, giải, giêng).
    # "qu" is an initial when followed by a vowel (qua, quân, quê).
    if best_initial_len >= 1:
        after = best_initial_len
        candidate = ''.join(_to_base_lower(c) for c in chars[:after + 1]) if after < n else ''
        if candidate in ('gi', 'qu') and after + 1 < n and _is_vowel_char(chars[after + 1]):
            best_initial_len = after + 1

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


def _get_vowel_nucleus_base(vowel_str):
    """Extract the base-lower vowel nucleus string from raw vowel chars."""
    return ''.join(_to_base_lower(c) for c in vowel_str)


def _get_tone_from_vowel(vowel_str):
    """Extract the tone index from a vowel string (takes the first toned vowel found).
    Returns 0 if no tone is present.
    """
    for ch in vowel_str:
        info = get_base_and_tone(ch)
        if info and info[1] != 0:
            return info[1]
    return 0


# Map plain vowels to their possible modified forms for prefix matching.
# When user types 'o', it could become 'ô' or 'ơ' via Telex transforms.
_VOWEL_COULD_BECOME = {
    'a': {'a', 'ă', 'â'},
    'e': {'e', 'ê'},
    'o': {'o', 'ô', 'ơ'},
    'u': {'u', 'ư'},
}


def _nucleus_could_match(typed_nucleus, valid_nucleus):
    """Check if a typed nucleus could become a valid nucleus via Telex transforms.
    Each plain vowel in the typed nucleus could become a modified vowel.
    """
    if len(typed_nucleus) > len(valid_nucleus):
        return False
    for i, ch in enumerate(typed_nucleus):
        if i >= len(valid_nucleus):
            return False
        possible = _VOWEL_COULD_BECOME.get(ch, {ch})
        if valid_nucleus[i] not in possible:
            return False
    return True


def _is_valid_nucleus(nucleus_base, allow_prefix=True):
    """Check if a vowel nucleus (base lowercase) is valid or a prefix of valid."""
    if nucleus_base in _VALID_VOWEL_NUCLEI:
        return True
    if allow_prefix:
        for vn in _VALID_VOWEL_NUCLEI:
            if _nucleus_could_match(nucleus_base, vn):
                return True
    return False


def is_complete_vietnamese(buffer):
    """Check if the buffer forms a complete valid Vietnamese syllable.

    Unlike is_valid_vietnamese() which allows prefixes (still-typing),
    this requires the syllable to be structurally complete:
    - Must have a vowel nucleus
    - Vowel nucleus must be in _VALID_VOWEL_NUCLEI (exact match, no prefix)
    - If has final consonant, it must be in VALID_FINALS and the (nucleus, final) pair valid
    - Tone + final compatibility must hold
    - Handles standalone consonant words like single-char initials

    Used at word boundaries to decide whether to restore original keystrokes.
    """
    if not buffer:
        return True

    initial, vowel, final = parse_syllable(buffer)
    initial_lower = ''.join(_to_base_lower(c) for c in initial)
    final_lower = ''.join(_to_base_lower(c) for c in final)
    nucleus_base = _get_vowel_nucleus_base(vowel)

    # Must have a vowel (except for standalone "gi" which can mean "gì" without explicit tone)
    if not vowel:
        return False

    # Initial must be valid
    if initial_lower and initial_lower not in VALID_INITIALS:
        return False

    # Nucleus must be an exact match (not a prefix)
    if nucleus_base not in _VALID_VOWEL_NUCLEI:
        return False

    # Initial + vowel compatibility
    if initial_lower in _INITIAL_LEADING_VOWEL and nucleus_base:
        leading_vowel = nucleus_base[0]
        allowed_leading = _INITIAL_LEADING_VOWEL[initial_lower]
        if leading_vowel not in allowed_leading:
            return False

    # Final consonant validation
    if final_lower:
        if final_lower not in VALID_FINALS:
            return False
        if nucleus_base in _NO_FINAL_NUCLEI:
            return False
        if (nucleus_base, final_lower) not in _VALID_VC_PAIRS:
            return False
        # Tone + checked final
        if final_lower in _CHECKED_FINALS:
            tone = _get_tone_from_vowel(vowel)
            if tone not in (0, 1, 5):
                return False
    else:
        # No final: nucleus must be a "complete" vowel sequence
        # (some like 'ie' are incomplete without a final — they need 'iê' + consonant)
        # For now, accept all nuclei in the valid set as potentially complete words
        pass

    return True


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

    # --- Validate vowel nucleus ---
    nucleus_base = _get_vowel_nucleus_base(vowel)
    if nucleus_base:
        # Always allow prefix/fuzzy match because the user may still transform
        # vowels via Telex (e.g., 'uo' could become 'uô' via oo->ô)
        if not _is_valid_nucleus(nucleus_base, allow_prefix=True):
            return False

    # --- Validate initial + vowel compatibility ---
    if initial_lower in _INITIAL_LEADING_VOWEL and nucleus_base:
        leading_vowel = nucleus_base[0]  # first base vowel of nucleus
        allowed_leading = _INITIAL_LEADING_VOWEL[initial_lower]
        # Also allow plain vowels that could become allowed via Telex transform
        leading_ok = leading_vowel in allowed_leading
        if not leading_ok:
            possible = _VOWEL_COULD_BECOME.get(leading_vowel, {leading_vowel})
            leading_ok = bool(possible & allowed_leading)
        if not leading_ok:
            return False

    # No final consonant yet - valid so far (still typing)
    if not final:
        return True

    # Has final consonant(s) - validate them
    valid_final = final_lower in VALID_FINALS
    prefix_final = False
    if not valid_final:
        for vf in VALID_FINALS:
            if vf.startswith(final_lower):
                prefix_final = True
                break
        if not prefix_final:
            return False

    # --- Validate nucleus that cannot take any final consonant ---
    # Only reject if the nucleus is exact match (already fully transformed)
    # Don't reject 'uo' which could become 'uô' (which allows finals)
    if valid_final and nucleus_base in _NO_FINAL_NUCLEI:
        if nucleus_base in _VALID_VOWEL_NUCLEI:
            # Exact known nucleus that can't take finals — but check if it
            # could also match a different nucleus that CAN take finals
            has_alternative = False
            for valid_nuc in _VALID_VOWEL_NUCLEI:
                if valid_nuc != nucleus_base and _nucleus_could_match(nucleus_base, valid_nuc):
                    if valid_nuc not in _NO_FINAL_NUCLEI:
                        has_alternative = True
                        break
            if not has_alternative:
                return False

    # --- Validate final + vowel compatibility via exhaustive pair table ---
    if valid_final and nucleus_base:
        if (nucleus_base, final_lower) not in _VALID_VC_PAIRS:
            # The nucleus might still be transformable (e.g., 'uo' -> 'uô' or 'ươ')
            # Check if any possible transformed nucleus would make a valid pair
            could_be_valid = False
            for valid_nuc in _VALID_VOWEL_NUCLEI:
                if _nucleus_could_match(nucleus_base, valid_nuc):
                    if (valid_nuc, final_lower) in _VALID_VC_PAIRS:
                        could_be_valid = True
                        break
            if not could_be_valid:
                return False

    # --- Validate tone + final compatibility (checked syllables) ---
    if valid_final and final_lower in _CHECKED_FINALS:
        tone = _get_tone_from_vowel(vowel)
        if tone not in (0, 1, 5):  # 0=no tone (still typing), 1=sắc, 5=nặng
            return False

    return True
