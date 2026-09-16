#!/usr/bin/env python3
"""Render the 1200x630 social card for every page of the site.

Cards are built from metadata already present in the HTML (og:title, the
post-meta line, and any figure the post embeds), so a post only needs its
normal front matter to get a card.

    pip install Pillow
    python3 scripts/generate_social_images.py

Output lands in assets/social/. Re-running is idempotent.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "social"
SITE = "https://juancopi81.github.io"

W, H = 1200, 630
MARGIN = 48          # gap between the canvas edge and the inner card
PAD = 64             # padding inside the inner card
RADIUS = 24
FIGURE_W = 372       # right-hand column when a post has a figure

# Pulled from styles.css :root so the cards match the site.
BG = "#fafafa"
CARD = "#ffffff"
BORDER = "#e4e4e7"
TEXT = "#18181b"
MUTED = "#71717a"
ACCENT = "#2563eb"

FONT_PATH = "/System/Library/Fonts/SFNS.ttf"


def font(size: int, weight: str = "Regular") -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(FONT_PATH, size)
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass  # Static fallback font: weight is whatever the file provides.
    return f


def wrap(draw, text: str, fnt, max_width: int) -> list[str]:
    lines, current = [], ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=fnt) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def fit_title(draw, text: str, max_width: int, max_lines: int,
              start: int = 64, floor: int = 40):
    """Shrink the title until it fits in max_lines, then return it wrapped."""
    for size in range(start, floor - 1, -2):
        fnt = font(size, "Bold")
        lines = wrap(draw, text, fnt, max_width)
        if len(lines) <= max_lines:
            return fnt, lines, size
    fnt = font(floor, "Bold")
    return fnt, wrap(draw, text, fnt, max_width)[:max_lines], floor


def base_card() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        [MARGIN, MARGIN, W - MARGIN, H - MARGIN],
        radius=RADIUS, fill=CARD, outline=BORDER, width=2,
    )
    return img, draw


def draw_eyebrow(draw, x: int, y: int, text: str) -> int:
    """Accent rule plus letterspaced label. Returns the next free y."""
    draw.rounded_rectangle([x, y, x + 56, y + 5], radius=3, fill=ACCENT)
    fnt = font(21, "Semibold")
    cursor, label_y = x, y + 26
    for ch in text.upper():
        draw.text((cursor, label_y), ch, font=fnt, fill=ACCENT)
        cursor += draw.textlength(ch, font=fnt) + 2.4  # manual letterspacing
    return label_y + 44


def paste_figure(img: Image.Image, figure: Path) -> None:
    box_x = W - MARGIN - PAD - FIGURE_W
    box_y, box_h = MARGIN + PAD, H - 2 * (MARGIN + PAD)
    fig = Image.open(figure).convert("RGB")
    scale = min(FIGURE_W / fig.width, box_h / fig.height)
    fig = fig.resize((max(1, int(fig.width * scale)), max(1, int(fig.height * scale))),
                     Image.LANCZOS)
    px = box_x + (FIGURE_W - fig.width) // 2
    py = box_y + (box_h - fig.height) // 2
    frame = ImageDraw.Draw(img)
    frame.rounded_rectangle([px - 12, py - 12, px + fig.width + 12, py + fig.height + 12],
                            radius=14, fill=CARD, outline=BORDER, width=2)
    img.paste(fig, (px, py))


def render(out_name: str, *, eyebrow: str, title: str, meta: str,
           figure: Path | None = None) -> Path:
    img, draw = base_card()
    x = MARGIN + PAD
    text_width = W - 2 * (MARGIN + PAD)
    if figure:
        text_width -= FIGURE_W + 44
        paste_figure(img, figure)

    y = draw_eyebrow(draw, x, MARGIN + PAD, eyebrow)
    fnt, lines, size = fit_title(draw, title, text_width, 3)
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=TEXT)
        y += int(size * 1.2)

    meta_font = font(23)
    baseline = H - MARGIN - PAD - 30
    if meta:
        draw.text((x, baseline), meta, font=meta_font, fill=MUTED)
    draw.text((x, baseline + 34), "juancopi81.github.io", font=font(23, "Medium"), fill=ACCENT)

    path = OUT / out_name
    img.save(path, "PNG", optimize=True)
    return path


def read(path: Path) -> str:
    return path.read_text()


def meta_of(text: str, key: str) -> str | None:
    m = re.search(rf'<meta (?:name|property)="{re.escape(key)}" content="([^"]*)" />', text)
    return html.unescape(m.group(1)) if m else None


def post_meta_line(text: str) -> str:
    m = re.search(r'(?s)<p class="post-meta">(.*?)</p>', text)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).split()) if m else ""


def first_figure(text: str) -> Path | None:
    m = re.search(r'assets/posts/([a-z0-9-]+\.png)', text)
    return (ROOT / "assets" / "posts" / m.group(1)) if m else None


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    made = []

    made.append(render(
        "default.png",
        eyebrow="Juan Carlos",
        title="Applied ML, generative AI, and research-to-production systems",
        meta="Senior ML Engineer · Music, creative AI, and diffusion research",
    ))

    for post in sorted((ROOT / "posts").glob("*.html")):
        text = read(post)
        title = meta_of(text, "og:title")
        if not title:
            print(f"skip (no og:title): {post.name}")
            continue
        made.append(render(
            post.with_suffix(".png").name,
            eyebrow="Research Log",
            title=title,
            meta=post_meta_line(text),
            figure=first_figure(text),
        ))

    for path in made:
        print(f"{path.relative_to(ROOT)}  ({path.stat().st_size // 1024} KB)")
    print(f"\n{len(made)} cards written to {OUT.relative_to(ROOT)}/")

    stale = []
    for post in sorted((ROOT / "posts").glob("*.html")):
        want = f"{SITE}/assets/social/{post.stem}.png"
        if meta_of(read(post), "og:image") != want:
            stale.append(post.name)
    if stale:
        print("\nThese posts do not point at their own card yet. Set og:image and")
        print("twitter:image to the matching URL, or the preview will 404:")
        for name in stale:
            print(f"  {name}  ->  {SITE}/assets/social/{Path(name).stem}.png")


if __name__ == "__main__":
    main()
