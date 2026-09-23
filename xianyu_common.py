"""Shared helpers for xianyu tuwen render scripts.

Extracted from render_codex55.py / render_workbuddy.py / render_winrar*.py
(similarity 87-97%%). New projects should import from here instead of
copying the ~100-line board/font/wrap boilerplate again.
"""
from PIL import Image, ImageDraw, ImageFont
import pathlib

FONT_REGULAR = r"C:/Windows/Fonts/msyh.ttc"
FONT_BOLD = r"C:/Windows/Fonts/msyhbd.ttc"


def get_font(size, bold=False, strict=True):
    """Load MSYH font; raise (not silent fallback) when missing by default."""
    path = FONT_BOLD if bold else FONT_REGULAR
    try:
        return ImageFont.truetype(path, size)
    except Exception as exc:
        if strict:
            raise RuntimeError("missing font file: %s (%s)" % (path, exc))
        return ImageFont.load_default()


def draw_board(w=1080, h=1080, border=38, blue=(47, 93, 255), radius=32):
    """Blue outer board + white rounded inner card. Returns (img, draw)."""
    im = Image.new("RGB", (w, h), blue)
    draw = ImageDraw.Draw(im)
    draw.rounded_rectangle(
        [border, border, w - border, h - border], radius=radius, fill="white"
    )
    return im, draw


def wrap_text(text, font, max_w, draw):
    """Char-level wrap by measured width. Returns list of lines."""
    lines, line = [], ""
    for ch in text:
        test = line + ch
        if draw.textlength(test, font=font) > max_w:
            lines.append(line)
            line = ch
        else:
            line = test
    if line:
        lines.append(line)
    return lines


def badge_geometry(draw, text, font, pad_x=40, height=42):
    """Centered pill-badge geometry: (width, height, x, y) for given canvas."""
    w = draw.textlength(text, font=font) + pad_x
    return w, height


def save_png(im, path):
    """mkdir -p + save PNG. Prints ascii-safe status, returns size in bytes."""
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    im.save(p, "PNG")
    size = p.stat().st_size
    print("saved %s bytes=%d" % (str(p), size))
    return size


def check_text_rules(title, body, forbidden, required):
    """Iron-rule self check.

    forbidden: iterable of substrings that must NOT appear.
    required: iterable of substrings that MUST appear.
    Returns list of violation codes (ascii), [] means pass.
    """
    violations = []
    for i, word in enumerate(forbidden):
        if word in title:
            violations.append("forbidden[%d]-in-title" % i)
        if word in body:
            violations.append("forbidden[%d]-in-body" % i)
    for i, word in enumerate(required):
        if word not in title and word not in body:
            violations.append("required[%d]-missing" % i)
    return violations
