"""Tests for telex_engine.py — Vietnamese Telex character composition."""

import pytest
from telex_engine import process_key, find_tone_target, get_base_and_tone, is_vowel


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def simulate(keys: str) -> str:
    """Type a sequence of keys through the engine and return the resulting text."""
    buf = []
    for ch in keys:
        buf, _bs, _info = process_key(buf, ch)
    return ''.join(buf)


def simulate_detailed(keys: str):
    """Return (result_text, buffer_list, last_backspace_count)."""
    buf = []
    bs = 0
    for ch in keys:
        buf, bs, _info = process_key(buf, ch)
    return ''.join(buf), buf, bs


# ---------------------------------------------------------------------------
# Vowel transforms
# ---------------------------------------------------------------------------

class TestVowelTransforms:
    """aa->â, ee->ê, oo->ô, aw->ă, ow->ơ, uw->ư"""

    @pytest.mark.parametrize("keys, expected", [
        ("aa", "â"),
        ("ee", "ê"),
        ("oo", "ô"),
        ("aw", "ă"),
        ("ow", "ơ"),
        ("uw", "ư"),
    ])
    def test_basic_vowel_transforms(self, keys, expected):
        assert simulate(keys) == expected

    @pytest.mark.parametrize("keys, expected", [
        ("aaa", "aa"),
        ("eee", "ee"),
        ("ooo", "oo"),
        ("aww", "aw"),
        ("oww", "ow"),
        ("uww", "uw"),
    ])
    def test_vowel_undo(self, keys, expected):
        assert simulate(keys) == expected

    def test_vowel_transform_preserves_case(self):
        assert simulate("AA") == "Â"
        assert simulate("OO") == "Ô"

    def test_w_transforms_u_in_word(self):
        assert simulate("tuw") == "tư"

    def test_w_transforms_o_in_word(self):
        assert simulate("tow") == "tơ"

    def test_w_transforms_rightmost_vowel(self):
        # In "thuo", w should transform o->ơ
        result = simulate("thuow")
        assert "ơ" in result


# ---------------------------------------------------------------------------
# Consonant D transforms
# ---------------------------------------------------------------------------

class TestConsonantD:

    def test_dd_to_d_stroke(self):
        assert simulate("dd") == "đ"

    def test_dd_uppercase(self):
        assert simulate("DD") == "Đ"

    def test_d_stroke_undo(self):
        # đ + d -> dd
        assert simulate("ddd") == "dd"

    def test_flexible_dd(self):
        # dod -> đo (d at start + vowel + d combines)
        assert simulate("dod") == "đo"

    def test_flexible_dd_longer(self):
        assert simulate("duongd") == "đuong"


# ---------------------------------------------------------------------------
# Tone marks
# ---------------------------------------------------------------------------

class TestToneMarks:
    """s=sắc, f=huyền, r=hỏi, x=ngã, j=nặng, z=remove"""

    @pytest.mark.parametrize("keys, expected", [
        ("as", "á"),
        ("af", "à"),
        ("ar", "ả"),
        ("ax", "ã"),
        ("aj", "ạ"),
    ])
    def test_single_vowel_tones(self, keys, expected):
        assert simulate(keys) == expected

    def test_tone_removal_with_z(self):
        assert simulate("asz") == "a"

    def test_same_tone_twice_outputs_literal(self):
        # á + s -> as (remove tone, append literal s)
        assert simulate("ass") == "as"

    def test_tone_on_modified_vowel(self):
        assert simulate("aas") == "ấ"   # â + sắc
        assert simulate("eef") == "ề"   # ê + huyền
        assert simulate("ooj") == "ộ"   # ô + nặng


# ---------------------------------------------------------------------------
# Tone placement rules
# ---------------------------------------------------------------------------

class TestTonePlacement:

    def test_single_vowel(self):
        assert simulate("ans") == "án"

    def test_penultimate_rule_no_final(self):
        # Two vowels, no final consonant -> tone on first (penultimate)
        assert simulate("muaf") == "mùa"

    def test_last_vowel_before_final_consonant(self):
        assert simulate("hoangf") == "hoàng"

    def test_modified_vowel_priority(self):
        # Single modified vowel among plain vowels gets priority
        assert simulate("hoawcs") == "hoắc"
        assert simulate("caanf") == "cần"

    def test_uo_diphthong_tone_on_second(self):
        """ươ/uô: tone always on the second vowel."""
        assert simulate("dduwowjc") == "được"
        assert simulate("nguwowif") == "người"
        assert simulate("nuwowcs") == "nước"
        assert simulate("uoongs") == "uống"
        assert simulate("muoons") == "muốn"
        assert simulate("cuoocj") == "cuộc"

    def test_uo_diphthong_tone_before_final(self):
        """Tone typed before final consonant should still go on second vowel."""
        assert simulate("dduwowjc") == simulate("dduwowcj")

    def test_qu_tone_not_on_u(self):
        # "qu" is consonant; tone should go on the actual vowel
        assert simulate("quaans") == "quấn"

    def test_gi_tone_not_on_i(self):
        # "gi" is consonant; tone should go on the actual vowel
        assert simulate("giair") == "giải"


# ---------------------------------------------------------------------------
# Full word integration tests
# ---------------------------------------------------------------------------

class TestFullWords:
    """End-to-end tests for common Vietnamese words."""

    @pytest.mark.parametrize("keys, expected", [
        # Basic words
        ("xin", "xin"),
        ("chaof", "chào"),
        ("vieejt", "việt"),
        ("nam", "nam"),
        ("khoong", "không"),
        ("khi", "khi"),
        ("dep", "dep"),

        # Tones
        ("ans", "án"),
        ("banj", "bạn"),
        ("lamf", "làm"),
        ("hocj", "học"),
        ("toor", "tổ"),
        ("ddef", "đè"),

        # â/ă family
        ("caanf", "cần"),
        ("laapj", "lập"),
        ("nawm", "năm"),
        ("bawts", "bắt"),
        ("taam", "tâm"),

        # ê family
        ("tees", "tế"),
        ("ddeemf", "đềm"),
        ("bieen", "biên"),

        # ô/ơ words
        ("toois", "tối"),
        ("buooir", "buổi"),
        ("mowis", "mới"),
        ("thowif", "thời"),
        ("chowf", "chờ"),

        # ươ words
        ("dduwowjc", "được"),
        ("nguwowif", "người"),
        ("nuwowcs", "nước"),
        ("dduwowngf", "đường"),
        ("truwowngf", "trường"),
        ("thuwowng", "thương"),
        ("thuwowngf", "thường"),
        ("cuwowif", "cười"),
        ("muwowif", "mười"),
        ("ruwowuj", "rượu"),
        ("luwowngf", "lường"),

        # uô words
        ("uoongs", "uống"),
        ("cuoocj", "cuộc"),
        ("muoons", "muốn"),

        # gi words
        ("giair", "giải"),
        ("giaos", "giáo"),
        ("nghix", "nghĩ"),

        # k/gh/ngh words
        ("keos", "kéo"),
        ("kees", "kế"),
        ("ghees", "ghế"),
        ("ngheef", "nghề"),

        # qu words
        ("quaan", "quân"),
        ("quaans", "quấn"),
        ("quoocs", "quốc"),
        ("quyeenf", "quyền"),

        # Checked syllable tones (sắc/nặng only with c/ch/p/t)
        ("cacs", "các"),
        ("cacj", "cạc"),
        ("bieets", "biết"),
        ("tieengs", "tiếng"),
        ("hoangf", "hoàng"),

        # oa/oe/oai
        ("ngoaif", "ngoài"),
    ])
    def test_word(self, keys, expected):
        assert simulate(keys) == expected


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestGiStandaloneTone:
    """#10: gi standalone tone handling — gì, gí, etc."""

    def test_gi_huyen(self):
        assert simulate("gif") == "gì"

    def test_gi_sac(self):
        assert simulate("gis") == "gí"

    def test_gi_hoi(self):
        assert simulate("gir") == "gỉ"

    def test_gi_nga(self):
        assert simulate("gix") == "gĩ"

    def test_gi_nang(self):
        assert simulate("gij") == "gị"

    def test_gi_remove_tone(self):
        assert simulate("gisz") == "gi"

    def test_gi_same_tone_twice(self):
        # gí + s -> gis (undo tone, append literal)
        assert simulate("giss") == "gis"

    def test_gi_uppercase(self):
        assert simulate("Gif") == "Gì"


class TestModernToneStyle:
    """#5: Modern vs traditional tone placement for oa, oe, uy."""

    def test_traditional_hoa(self):
        import config
        config.tone_style = 'old'
        assert simulate("hoaf") == "hòa"

    def test_modern_hoa(self):
        import config
        config.tone_style = 'new'
        result = simulate("hoaf")
        config.tone_style = 'old'  # restore
        assert result == "hoà"

    def test_traditional_hoe(self):
        import config
        config.tone_style = 'old'
        assert simulate("hoer") == "hỏe"

    def test_modern_hoe(self):
        import config
        config.tone_style = 'new'
        result = simulate("hoer")
        config.tone_style = 'old'
        assert result == "hoẻ"

    def test_traditional_thuy(self):
        import config
        config.tone_style = 'old'
        assert simulate("thuyf") == "thùy"

    def test_modern_thuy(self):
        import config
        config.tone_style = 'new'
        result = simulate("thuyf")
        config.tone_style = 'old'
        assert result == "thuỳ"

    def test_non_oa_oe_uy_unaffected(self):
        """Other diphthongs should not be affected by modern style."""
        import config
        config.tone_style = 'new'
        result = simulate("muaf")
        config.tone_style = 'old'
        assert result == "mùa"  # ua is not oa/oe/uy, so still traditional


class TestEdgeCases:

    def test_empty_buffer_tone_key(self):
        # Tone key on empty buffer should just output the key
        assert simulate("s") == "s"
        assert simulate("f") == "f"

    def test_non_alpha_passthrough(self):
        assert simulate("123") == "123"

    def test_backspace_count_on_transform(self):
        _, _, bs = simulate_detailed("dd")
        assert bs == 1  # erase 'd', type 'đ'

    def test_backspace_count_on_tone(self):
        _, _, bs = simulate_detailed("ans")
        assert bs == 2  # erase 'an' (2 chars), retype 'án'

    def test_no_transform_returns_zero_backspace(self):
        _, _, bs = simulate_detailed("abc")
        assert bs == 0

    def test_uppercase_preservation_in_tone(self):
        assert simulate("As") == "Á"
        assert simulate("AAs") == "Ấ"
