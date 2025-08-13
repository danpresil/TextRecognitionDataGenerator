import os
import textwrap
from typing import List, Tuple

from trdg.data_generator import FakeTextDataGenerator
from trdg.utils import load_fonts, font_has_glyph

# support RTL
from arabic_reshaper import ArabicReshaper
from bidi.algorithm import get_display


class GeneratorFromStrings:
    """Generator that uses a given list of strings"""

    def __init__(
        self,
        strings: List[str],
        count: int = -1,
        fonts: List[str] = [],
        language: str = "en",
        size: int = 32,
        skewing_angle: int = 0,
        random_skew: bool = False,
        blur: int = 0,
        random_blur: bool = False,
        background_type: int = 0,
        distorsion_type: int = 0,
        distorsion_orientation: int = 0,
        is_handwritten: bool = False,
        width: int = -1,
        alignment: int = 1,
        text_color: str = "#282828",
        orientation: int = 0,
        space_width: float = 1.0,
        character_spacing: int = 0,
        margins: Tuple[int, int, int, int] = (5, 5, 5, 5),
        fit: bool = False,
        output_mask: bool = False,
        word_split: bool = False,
        image_dir: str = os.path.join(
            "..", os.path.split(os.path.realpath(__file__))[0], "images"
        ),
        stroke_width: int = 0,
        stroke_fill: str = "#282828",
        image_mode: str = "RGB",
        output_bboxes: int = 0,
        rtl: bool = False,
        max_line_length: int = 0,
    ):
        self.count = count
        self.fonts = fonts if len(fonts) > 0 else load_fonts(language)
        self.language = language
        self.size = size
        self.skewing_angle = skewing_angle
        self.random_skew = random_skew
        self.blur = blur
        self.random_blur = random_blur
        self.background_type = background_type
        self.distorsion_type = distorsion_type
        self.distorsion_orientation = distorsion_orientation
        self.is_handwritten = is_handwritten
        self.width = width
        self.rtl = rtl
        # When generating right-to-left text, default to left alignment
        # so the rendered text starts near the image's left edge unless a
        # different alignment is explicitly requested.
        self.alignment = 0 if self.rtl and alignment == 1 else alignment
        self.text_color = text_color
        self.orientation = orientation
        self.space_width = space_width
        self.character_spacing = character_spacing
        self.margins = margins
        self.fit = fit
        self.output_mask = output_mask
        self.word_split = word_split
        self.image_dir = image_dir
        self.output_bboxes = output_bboxes
        self.generated_count = 0
        self.stroke_width = stroke_width
        self.stroke_fill = stroke_fill
        self.image_mode = image_mode
        self.max_line_length = max_line_length

        if self.rtl:
            if language == "ckb":
                ar_reshaper_config = {"delete_harakat": True, "language": "Kurdish"}
            else:
                ar_reshaper_config = {"delete_harakat": False}
            self.rtl_shaper = ArabicReshaper(configuration=ar_reshaper_config)
        else:
            self.rtl_shaper = None

        self.set_strings(strings)

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        if self.generated_count == self.count:
            raise StopIteration
        self.generated_count += 1
        font = self.fonts[(self.generated_count - 1) % len(self.fonts)]
        idx = (self.generated_count - 1) % len(self.strings)
        string = self.strings[idx]
        result = FakeTextDataGenerator.generate(
            self.generated_count,
            string,
            font,
            None,
            self.size,
            None,
            self.skewing_angle,
            self.random_skew,
            self.blur,
            self.random_blur,
            self.background_type,
            self.distorsion_type,
            self.distorsion_orientation,
            self.is_handwritten,
            0,
            self.width,
            self.alignment,
            self.text_color,
            self.orientation,
            self.space_width,
            self.character_spacing,
            self.margins,
            self.fit,
            self.output_mask,
            self.word_split,
            self.image_dir,
            self.stroke_width,
            self.stroke_fill,
            self.image_mode,
            self.output_bboxes,
        )

        if self.output_mask:
            image, mask, _label = result
        else:
            image, _label = result

        # Use original, unreshaped strings for labels when generating RTL text
        label = self.orig_strings[idx] if self.rtl else _label
        label = "".join(
            c for c in label if c in [" ", "\n"] or font_has_glyph(font, c)
        )

        if self.output_mask:
            return image, mask, label
        return image, label

    def set_strings(self, strings: List[str]):
        wrapped = [self._wrap_text(s) for s in strings]
        # Keep a copy of the original strings so that labels remain in their
        # natural order even when RTL reshaping is applied later on.
        self.orig_strings = list(wrapped)
        if self.rtl:
            self.strings = self.reshape_rtl(wrapped, self.rtl_shaper)
        else:
            self.strings = wrapped

    def _wrap_text(self, text: str) -> str:
        if self.max_line_length and self.max_line_length > 0:
            lines = []
            for line in text.split("\n"):
                lines.extend(
                    textwrap.wrap(
                        line,
                        width=self.max_line_length,
                        break_long_words=False,
                        break_on_hyphens=False,
                    )
                )
            return "\n".join(lines)
        return text

    def reshape_rtl(self, strings: list, rtl_shaper: ArabicReshaper):
        # reshape RTL characters before generating any image
        rtl_strings = []
        for string in strings:
            reshaped_string = rtl_shaper.reshape(string)
            rtl_strings.append(get_display(reshaped_string))
        return rtl_strings


if __name__ == "__main__":
    from trdg.generators.from_wikipedia import GeneratorFromWikipedia

    s = GeneratorFromWikipedia("test")
    next(s)
