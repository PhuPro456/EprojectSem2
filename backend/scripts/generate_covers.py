"""Regenerate every book cover SVG from the catalog in app.db.mock_data.

Run from the backend folder:

    python scripts/generate_covers.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.db.mock_data import BOOKS  # noqa: E402

COVER_DIR = BACKEND_DIR.parent / "frontend" / "static" / "covers"

WIDTH, HEIGHT = 300, 440
TEXT_LEFT = 36
MAX_TEXT_WIDTH = 228

BACKGROUNDS = (
    "#132b40",
    "#302342",
    "#24463d",
    "#673040",
    "#134f56",
    "#304858",
    "#303f69",
    "#54483c",
    "#513f61",
    "#663f30",
)

CATEGORY_ACCENTS = {
    "Romance": "#e5a7a0",
    "Fiction": "#f1d89d",
    "Fantasy": "#b4d9d4",
    "Mystery": "#f0bb78",
    "Science Fiction": "#9fc6d8",
}
FALLBACK_ACCENT = "#e8c978"

# Character widths as a fraction of the font size, for Georgia bold.
NARROW = set("iljtfrI.,':;|!()[]")
WIDE = set("mwMW")
LOWER_WIDE = set("abcdeghknopqsuvxyz")


def _char_width(char: str, size: float) -> float:
    if char == " ":
        return 0.28 * size
    if char in NARROW:
        return 0.32 * size
    if char in WIDE:
        return 0.88 * size
    if char.isupper():
        return 0.70 * size
    if char in LOWER_WIDE:
        return 0.58 * size
    return 0.50 * size


def text_width(text: str, size: float) -> float:
    # 1.12 calibrates the estimate against Georgia bold measured in a browser.
    return sum(_char_width(char, size) for char in text) * 1.12


def wrap(title: str, size: float) -> list[str]:
    words = title.split()
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if text_width(candidate, size) <= MAX_TEXT_WIDTH:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def title_lines(title: str) -> tuple[list[str], float]:
    for size in (29.0, 25.0, 22.0, 19.0):
        lines = wrap(title, size)
        if len(lines) <= 3 and all(
            text_width(line, size) <= MAX_TEXT_WIDTH for line in lines
        ):
            return lines, size
    return wrap(title, 19.0), 19.0


def escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_cover(index: int, book: dict) -> str:
    accent = CATEGORY_ACCENTS.get(book["category"], FALLBACK_ACCENT)
    background = BACKGROUNDS[index % len(BACKGROUNDS)]
    radius = 52 + (index * 7) % 19
    crest = 258 + (index * 11) % 36

    lines, size = title_lines(book["title"])
    line_height = round(size * 1.34, 1)
    first_baseline = round(210 - (len(lines) - 1) * line_height / 2, 1)

    author = book["author"]
    author_size = 14 if text_width(author, 14) <= MAX_TEXT_WIDTH else 12

    title_markup = "".join(
        f'<text x="{TEXT_LEFT}" y="{round(first_baseline + n * line_height, 1)}" '
        f'font-family="Georgia,serif" font-size="{size:g}" font-weight="bold" '
        f'fill="#fff">{escape(line)}</text>'
        for n, line in enumerate(lines)
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}">'
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{background}"/>'
        f'<rect x="16" y="16" width="268" height="408" fill="none" '
        f'stroke="{accent}" stroke-width="2"/>'
        f'<circle cx="232" cy="116" r="{radius}" fill="{accent}" opacity=".8"/>'
        f'<circle cx="232" cy="116" r="31" fill="{background}" opacity=".85"/>'
        f'<path d="M0 335 Q75 {crest} 150 340 T300 325 V440 H0Z" '
        f'fill="{accent}" opacity=".20"/>'
        f'<text x="{TEXT_LEFT}" y="58" font-family="Arial,sans-serif" font-size="12" '
        f'letter-spacing="2" fill="{accent}">{escape(book["category"].upper())}</text>'
        f"{title_markup}"
        f'<line x1="36" y1="365" x2="104" y2="365" stroke="{accent}" stroke-width="3"/>'
        f'<text x="{TEXT_LEFT}" y="392" font-family="Arial,sans-serif" '
        f'font-size="{author_size}" fill="white">{escape(author)}</text>'
        f'<text x="{TEXT_LEFT}" y="411" font-family="Arial,sans-serif" font-size="9" '
        f'letter-spacing="1.5" fill="{accent}">PAPER &amp; PINE BOOKSTORE</text>'
        "</svg>"
    )


def main() -> None:
    COVER_DIR.mkdir(parents=True, exist_ok=True)
    for index, book in enumerate(BOOKS):
        filename = book["cover"].rsplit("/", 1)[-1]
        (COVER_DIR / filename).write_text(build_cover(index, book), encoding="utf-8")
    print(f"Wrote {len(BOOKS)} covers to {COVER_DIR}")


if __name__ == "__main__":
    main()
