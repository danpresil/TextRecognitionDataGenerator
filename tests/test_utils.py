from trdg.utils import font_has_glyph, filter_fonts_for_text


def test_font_has_glyph():
    assert font_has_glyph("tests/font.ttf", "A")
    assert not font_has_glyph("tests/font.ttf", "ش")


def test_filter_fonts_for_text():
    fonts = ["tests/font.ttf", "tests/font_ar.ttf"]
    assert filter_fonts_for_text("A", fonts) == ["tests/font.ttf"]
    assert filter_fonts_for_text("ش", fonts) == ["tests/font_ar.ttf"]
    assert filter_fonts_for_text("Aش", fonts) == []
