import os
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
