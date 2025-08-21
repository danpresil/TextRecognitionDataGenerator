import random as rnd
from typing import Optional, Tuple
from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont

from trdg.utils import get_text_width, get_text_height, font_has_glyph

# Thai Unicode reference: https://jrgraphix.net/r/Unicode/0E00-0E7F
TH_TONE_MARKS = [
    "0xe47",
    "0xe48",
    "0xe49",
    "0xe4a",
    "0xe4b",
    "0xe4c",
    "0xe4d",
    "0xe4e",
]
TH_UNDER_VOWELS = ["0xe38", "0xe39", "\0xe3A"]
TH_UPPER_VOWELS = ["0xe31", "0xe34", "0xe35", "0xe36", "0xe37"]


# Internal helper to decide which font should be used for a given character
def _select_font_for_char(
    character: str,
    font_path: str,
    image_font: ImageFont,
    missing_glyph_strategy: str,
    fallback_font: Optional[ImageFont] = None,
    fallback_font_path: Optional[str] = None,
):
    if character == " ":
        return image_font

    if font_has_glyph(font_path, character):
        return image_font

    if (
        missing_glyph_strategy == "fallback"
        and fallback_font
        and fallback_font_path
        and font_has_glyph(fallback_font_path, character)
    ):
        return fallback_font

    return None


def generate(
    text: str,
    font: str,
    text_color: str,
    font_size: int,
    orientation: int,
    space_width: int,
    character_spacing: int,
    fit: bool,
    word_split: bool,
    stroke_width: int = 0,
    stroke_fill: str = "#282828",
    missing_glyph_strategy: str = "fallback",
    fallback_font: Optional[str] = None,
    alignment: int = 0,
) -> Tuple:
    if orientation == 0:
        return _generate_horizontal_text(
            text,
            font,
            text_color,
            font_size,
            space_width,
            character_spacing,
            fit,
            word_split,
            stroke_width,
            stroke_fill,
            missing_glyph_strategy,
            fallback_font,
            alignment,
        )
    elif orientation == 1:
        return _generate_vertical_text(
            text,
            font,
            text_color,
            font_size,
            space_width,
            character_spacing,
            fit,
            stroke_width,
            stroke_fill,
            missing_glyph_strategy,
            fallback_font,
            alignment,
        )
    else:
        raise ValueError("Unknown orientation " + str(orientation))


def _compute_character_width(
    image_font: ImageFont,
    font_path: str,
    character: str,
    missing_glyph_strategy: str,
    fallback_font: Optional[ImageFont] = None,
    fallback_font_path: Optional[str] = None,
) -> int:
    if len(character) == 1 and (
        "{0:#x}".format(ord(character))
        in TH_TONE_MARKS + TH_UNDER_VOWELS + TH_UNDER_VOWELS + TH_UPPER_VOWELS
    ):
        return 0

    selected_font = _select_font_for_char(
        character,
        font_path,
        image_font,
        missing_glyph_strategy,
        fallback_font,
        fallback_font_path,
    )
    if selected_font is None:
        return 0

    # Casting as int to preserve the old behavior
    return round(selected_font.getlength(character))


def _generate_horizontal_text(
    text: str,
    font: str,
    text_color: str,
    font_size: int,
    space_width: int,
    character_spacing: int,
    fit: bool,
    word_split: bool,
    stroke_width: int = 0,
    stroke_fill: str = "#282828",
    missing_glyph_strategy: str = "fallback",
    fallback_font: Optional[str] = None,
    alignment: int = 0,
) -> Tuple:
    image_font = ImageFont.truetype(font=font, size=font_size)
    fallback_image_font = (
        ImageFont.truetype(font=fallback_font, size=font_size)
        if fallback_font
        else None
    )

    space_width = int(get_text_width(image_font, " ") * space_width)

    lines = text.replace("\\n", "\n").replace("/n", "\n").split("\n")

    line_chars = []
    line_widths = []
    line_heights = []
    rendered_lines = []

    for line in lines:
        chars_info = []
        rendered_line = []
        for c in line:
            if c == " ":
                chars_info.append((c, space_width, image_font))
                rendered_line.append(c)
                continue

            selected_font = _select_font_for_char(
                c,
                font,
                image_font,
                missing_glyph_strategy,
                fallback_image_font,
                fallback_font,
            )
            if selected_font is None:
                continue

            width = _compute_character_width(
                image_font,
                font,
                c,
                missing_glyph_strategy,
                fallback_image_font,
                fallback_font,
            )
            chars_info.append((c, width, selected_font))
            rendered_line.append(c)

        line_width = sum(w for _, w, _ in chars_info)
        if not word_split:
            line_width += character_spacing * (len(chars_info) - 1)

        if chars_info:
            line_height = max(
                [get_text_height(f, ch) for ch, _, f in chars_info]
            )
        else:
            line_height = get_text_height(image_font, " ")

        line_chars.append(chars_info)
        line_widths.append(line_width)
        line_heights.append(line_height)
        rendered_lines.append("".join(rendered_line))

    text_width = max(line_widths) if line_widths else 0
    text_height = sum(line_heights)

    txt_img = Image.new("RGBA", (text_width, text_height), (0, 0, 0, 0))
    txt_mask = Image.new("RGB", (text_width, text_height), (0, 0, 0))

    txt_img_draw = ImageDraw.Draw(txt_img)
    txt_mask_draw = ImageDraw.Draw(txt_mask, mode="RGB")
    txt_mask_draw.fontmode = "1"

    colors = [ImageColor.getrgb(c) for c in text_color.split(",")]
    c1, c2 = colors[0], colors[-1]

    fill = (
        rnd.randint(min(c1[0], c2[0]), max(c1[0], c2[0])),
        rnd.randint(min(c1[1], c2[1]), max(c1[1], c2[1])),
        rnd.randint(min(c1[2], c2[2]), max(c1[2], c2[2])),
    )

    stroke_colors = [ImageColor.getrgb(c) for c in stroke_fill.split(",")]
    stroke_c1, stroke_c2 = stroke_colors[0], stroke_colors[-1]

    stroke_fill = (
        rnd.randint(min(stroke_c1[0], stroke_c2[0]), max(stroke_c1[0], stroke_c2[0])),
        rnd.randint(min(stroke_c1[1], stroke_c2[1]), max(stroke_c1[1], stroke_c2[1])),
        rnd.randint(min(stroke_c1[2], stroke_c2[2]), max(stroke_c1[2], stroke_c2[2])),
    )

    char_index = 0
    y_offset = 0
    for chars_info, line_height, line_width in zip(line_chars, line_heights, line_widths):
        if alignment == 1:
            x_offset = (text_width - line_width) // 2
        elif alignment == 2:
            x_offset = text_width - line_width
        else:
            x_offset = 0
        for i, (ch, width, fnt) in enumerate(chars_info):
            txt_img_draw.text(
                (
                    x_offset + i * character_spacing * int(not word_split),
                    y_offset,
                ),
                ch,
                fill=fill,
                font=fnt,
                stroke_width=stroke_width,
                stroke_fill=stroke_fill,
            )
            txt_mask_draw.text(
                (
                    x_offset + i * character_spacing * int(not word_split),
                    y_offset,
                ),
                ch,
                fill=
                (
                    (char_index + 1) // (255 * 255),
                    (char_index + 1) // 255,
                    (char_index + 1) % 255,
                ),
                font=fnt,
                stroke_width=stroke_width,
                stroke_fill=stroke_fill,
            )
            x_offset += width
            char_index += 1
        y_offset += line_height
    label = "\n".join(rendered_lines)

    if fit:
        return (
            txt_img.crop(txt_img.getbbox()),
            txt_mask.crop(txt_img.getbbox()),
            label,
        )
    else:
        return txt_img, txt_mask, label


def _generate_vertical_text(
    text: str,
    font: str,
    text_color: str,
    font_size: int,
    space_width: int,
    character_spacing: int,
    fit: bool,
    stroke_width: int = 0,
    stroke_fill: str = "#282828",
    missing_glyph_strategy: str = "fallback",
    fallback_font: Optional[str] = None,
    alignment: int = 0,
) -> Tuple:
    image_font = ImageFont.truetype(font=font, size=font_size)
    fallback_image_font = (
        ImageFont.truetype(font=fallback_font, size=font_size)
        if fallback_font
        else None
    )

    space_height = int(get_text_height(image_font, " ") * space_width)

    chars_info = []
    rendered_chars = []
    for c in text:
        if c == " ":
            height = space_height
            width = get_text_width(image_font, c)
            chars_info.append((c, width, height, image_font))
            rendered_chars.append(c)
            continue

        selected_font = _select_font_for_char(
            c,
            font,
            image_font,
            missing_glyph_strategy,
            fallback_image_font,
            fallback_font,
        )
        if selected_font is None:
            continue

        width = get_text_width(selected_font, c)
        height = get_text_height(selected_font, c)
        chars_info.append((c, width, height, selected_font))
        rendered_chars.append(c)

    text_width = max([w for _, w, _, _ in chars_info]) if chars_info else 0
    text_height = (
        sum([h for _, _, h, _ in chars_info])
        + character_spacing * len(chars_info)
    )

    txt_img = Image.new("RGBA", (text_width, text_height), (0, 0, 0, 0))
    txt_mask = Image.new("RGBA", (text_width, text_height), (0, 0, 0, 0))

    txt_img_draw = ImageDraw.Draw(txt_img)
    txt_mask_draw = ImageDraw.Draw(txt_mask)
    txt_mask_draw.fontmode = "1"

    colors = [ImageColor.getrgb(c) for c in text_color.split(",")]
    c1, c2 = colors[0], colors[-1]

    fill = (
        rnd.randint(c1[0], c2[0]),
        rnd.randint(c1[1], c2[1]),
        rnd.randint(c1[2], c2[2]),
    )

    stroke_colors = [ImageColor.getrgb(c) for c in stroke_fill.split(",")]
    stroke_c1, stroke_c2 = stroke_colors[0], stroke_colors[-1]

    stroke_fill = (
        rnd.randint(stroke_c1[0], stroke_c2[0]),
        rnd.randint(stroke_c1[1], stroke_c2[1]),
        rnd.randint(stroke_c1[2], stroke_c2[2]),
    )

    char_index = 0
    y_offset = 0
    for c, width, height, fnt in chars_info:
        txt_img_draw.text(
            (0, y_offset),
            c,
            fill=fill,
            font=fnt,
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
        )
        txt_mask_draw.text(
            (0, y_offset),
            c,
            fill=((char_index + 1) // (255 * 255), (char_index + 1) // 255, (char_index + 1) % 255),
            font=fnt,
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
        )
        y_offset += height + character_spacing
        char_index += 1
    label = "".join(rendered_chars)

    if fit:
        return (
            txt_img.crop(txt_img.getbbox()),
            txt_mask.crop(txt_img.getbbox()),
            label,
        )
    else:
        return txt_img, txt_mask, label
