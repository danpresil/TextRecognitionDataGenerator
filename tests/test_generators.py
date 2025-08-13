import os
from PIL import ImageOps
from trdg.generators.from_strings import GeneratorFromStrings

def test_max_line_length_wraps_without_breaking_words():
    test_font = os.path.join(os.path.dirname(__file__), 'font.ttf')
    gen = GeneratorFromStrings(
        ['This is a very long sentence'],
        fonts=[test_font],
        max_line_length=10,
    )
    img, label = next(gen)
    assert label == 'This is a\nvery long\nsentence'

def test_rtl_text_is_left_aligned():
    test_font = os.path.join(os.path.dirname(__file__), 'font_ar.ttf')
    gen = GeneratorFromStrings(
        ['مرحبا'],
        fonts=[test_font],
        language='ar',
        rtl=True,
        width=200,
        background_type=1,
    )
    img, _ = next(gen)
    bbox = ImageOps.invert(img.convert('L')).getbbox()
    # Left edge should be within 5px of image left
    assert bbox[0] <= 5
    # Right edge should have some margin (>5px)
    assert img.width - bbox[2] > 5
