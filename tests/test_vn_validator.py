"""Tests for vn_validator.py — Vietnamese syllable structure validation."""

import pytest
from vn_validator import is_valid_vietnamese, parse_syllable


# ---------------------------------------------------------------------------
# Syllable parsing
# ---------------------------------------------------------------------------

class TestParseSyllable:

    def test_empty(self):
        assert parse_syllable([]) == ('', '', '')

    def test_consonant_only(self):
        init, vowel, final = parse_syllable(list('th'))
        assert init == 'th'
        assert vowel == ''
        assert final == ''

    def test_simple_syllable(self):
        init, vowel, final = parse_syllable(list('nam'))
        assert init == 'n'
        assert vowel == 'a'
        assert final == 'm'

    def test_compound_initial(self):
        init, vowel, final = parse_syllable(list('ngh'))
        assert init == 'ngh'

    def test_compound_final(self):
        init, vowel, final = parse_syllable(list('anh'))
        assert final == 'nh'

    def test_gi_initial_before_vowel(self):
        """gi is parsed as initial when followed by another vowel."""
        init, vowel, final = parse_syllable(list('giai'))
        assert init == 'gi'
        assert vowel == 'ai'

    def test_gi_alone(self):
        """gi alone: g is initial, i is vowel."""
        init, vowel, final = parse_syllable(list('gi'))
        assert init == 'g'
        assert vowel == 'i'

    def test_qu_initial_before_vowel(self):
        init, vowel, final = parse_syllable(list('qua'))
        assert init == 'qu'
        assert vowel == 'a'

    @pytest.mark.parametrize("word, expected_init", [
        ("gia", "gi"),
        ("qua", "qu"),
        ("que", "qu"),   # wait, q-u-e: qu + e
        ("thi", "th"),
        ("nghi", "ngh"),
    ])
    def test_initial_parsing(self, word, expected_init):
        init, _, _ = parse_syllable(list(word))
        assert init == expected_init


# ---------------------------------------------------------------------------
# Tone-final consonant rules (checked syllables)
# ---------------------------------------------------------------------------

class TestCheckedSyllableTones:
    """Syllables ending in -c, -ch, -p, -t can only have sắc (1) or nặng (5)."""

    @pytest.mark.parametrize("word", [
        list("các"),     # c + sắc
        list("cạc"),     # c + nặng
        list("hắc"),     # c + sắc
        list("mát"),     # t + sắc
        list("mạt"),     # t + nặng
        list("hấp"),     # p + sắc
        list("hập"),     # p + nặng
        list("hạch"),    # ch + nặng
        list("sách"),    # ch + sắc
        list("biết"),    # t + sắc
        list("việt"),    # t + nặng
        list("học"),     # c + nặng
    ])
    def test_valid_checked_tones(self, word):
        assert is_valid_vietnamese(word) is True

    @pytest.mark.parametrize("word", [
        list("hảch"),    # ch + hỏi -> INVALID
        list("hãc"),     # c + ngã -> INVALID
        list("hảp"),     # p + hỏi -> INVALID
        list("mãt"),     # t + ngã -> INVALID
        list("hàc"),     # c + huyền -> INVALID
        list("hãp"),     # p + ngã -> INVALID
    ])
    def test_invalid_checked_tones(self, word):
        assert is_valid_vietnamese(word) is False

    @pytest.mark.parametrize("word", [
        list("hàm"),     # m + huyền -> OK (unchecked)
        list("hản"),     # n + hỏi -> OK
        list("hãng"),    # ng + ngã -> OK
        list("hành"),    # nh + huyền -> OK
    ])
    def test_unchecked_finals_allow_all_tones(self, word):
        assert is_valid_vietnamese(word) is True


# ---------------------------------------------------------------------------
# Vowel nuclei validation
# ---------------------------------------------------------------------------

class TestVowelNuclei:

    @pytest.mark.parametrize("word", [
        list("hoai"),    # oai
        list("oan"),     # oa
        list("hoe"),     # oe
        list("uôi"),     # uôi
        list("ươi"),     # ươi
    ])
    def test_valid_nuclei(self, word):
        assert is_valid_vietnamese(word) is True

    @pytest.mark.parametrize("word, desc", [
        (list("tưeng"), "ưe is not a valid nucleus"),
    ])
    def test_invalid_nuclei(self, word, desc):
        assert is_valid_vietnamese(word) is False, desc


# ---------------------------------------------------------------------------
# Initial + vowel compatibility
# ---------------------------------------------------------------------------

class TestInitialVowelCompat:

    @pytest.mark.parametrize("word", [
        list("ki"),
        list("ke"),
        list("kê"),
        list("ky"),
        list("keo"),     # k + e (leading vowel e is allowed)
        list("kế"),
    ])
    def test_k_valid_vowels(self, word):
        assert is_valid_vietnamese(word) is True

    @pytest.mark.parametrize("word", [
        list("ka"),
        list("ko"),
        list("ku"),
    ])
    def test_k_invalid_vowels(self, word):
        assert is_valid_vietnamese(word) is False

    @pytest.mark.parametrize("word", [
        list("ghi"),
        list("ghe"),
        list("ghê"),
        list("ghế"),
    ])
    def test_gh_valid_vowels(self, word):
        assert is_valid_vietnamese(word) is True

    @pytest.mark.parametrize("word", [
        list("gha"),
        list("gho"),
        list("ghu"),
    ])
    def test_gh_invalid_vowels(self, word):
        assert is_valid_vietnamese(word) is False

    @pytest.mark.parametrize("word", [
        list("nghi"),
        list("nghê"),
        list("nghĩ"),
    ])
    def test_ngh_valid_vowels(self, word):
        assert is_valid_vietnamese(word) is True

    @pytest.mark.parametrize("word", [
        list("ngha"),
        list("ngho"),
    ])
    def test_ngh_invalid_vowels(self, word):
        assert is_valid_vietnamese(word) is False


# ---------------------------------------------------------------------------
# Final + vowel compatibility
# ---------------------------------------------------------------------------

class TestFinalVowelCompat:

    @pytest.mark.parametrize("word", [
        list("ách"),     # a + ch
        list("ích"),     # i + ch
        list("êch"),     # ê + ch
        list("anh"),     # a + nh
        list("inh"),     # i + nh
        list("ênh"),     # ê + nh
    ])
    def test_ch_nh_valid_vowels(self, word):
        assert is_valid_vietnamese(word) is True

    @pytest.mark.parametrize("word", [
        list("ôch"),     # ô + ch -> INVALID
        list("ưch"),     # ư + ch -> INVALID
        list("ưnh"),     # ư + nh -> INVALID
        list("ônh"),     # ô + nh -> INVALID
    ])
    def test_ch_nh_invalid_vowels(self, word):
        assert is_valid_vietnamese(word) is False


# ---------------------------------------------------------------------------
# Prefix typing (partial words should be valid while typing)
# ---------------------------------------------------------------------------

class TestPrefixTyping:

    @pytest.mark.parametrize("partial", [
        list("t"),
        list("th"),
        list("thu"),
        list("thuo"),     # uo could become uô via Telex
        list("thuon"),
        list("thuong"),
        list("ngu"),
        list("nguo"),
        list("n"),
        list("ng"),
        list("ngh"),
    ])
    def test_partial_words_are_valid(self, partial):
        assert is_valid_vietnamese(partial) is True

    def test_empty_is_valid(self):
        assert is_valid_vietnamese([]) is True


# ---------------------------------------------------------------------------
# Common Vietnamese words (integration)
# ---------------------------------------------------------------------------

class TestCommonWords:

    @pytest.mark.parametrize("word", [
        "xin", "chào", "việt", "nam", "được", "không", "người",
        "thương", "quân", "khi", "hoàng", "giải", "kéo",
        "ghế", "nghĩ", "nghề", "quốc", "quyền", "biết",
        "tiếng", "nước", "đường", "trường", "cười", "mười",
        "rượu", "uống", "cuộc", "muốn", "mới", "thời",
        "học", "các", "lập", "cần", "năm", "bắt",
        "tâm", "tế", "biên", "tối", "buổi",
        "mùa", "án", "bạn", "làm", "tổ", "đè",
        "anh", "sinh", "hành",
    ])
    def test_valid_word(self, word):
        assert is_valid_vietnamese(list(word)) is True, f"'{word}' should be valid"
