"""
Generate terminal-style PNG screenshots for each recommender profile output.
Saves images to docs/screenshots/.
"""

import os
import sys
import subprocess
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BG_COLOR      = (30, 30, 30)          # dark terminal background
FG_COLOR      = (220, 220, 220)       # default text
ACCENT_COLOR  = (100, 210, 255)       # section headers / separators
SCORE_COLOR   = (180, 255, 120)       # score lines
BULLET_COLOR  = (255, 200, 80)        # bullet reason lines
TITLE_COLOR   = (255, 255, 255)       # song title lines
HEADER_COLOR  = (255, 180, 60)        # profile banner

FONT_SIZE     = 18
PADDING       = 28                    # px around the text block
LINE_SPACING  = 6                     # extra px between lines
BORDER_RADIUS = 12
TOP_BAR_H     = 36                    # macOS-style traffic-light bar height

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "screenshots")


def get_font(size=FONT_SIZE, bold=False):
    """Return a monospace font, falling back to default if not found."""
    candidates = [
        "/System/Library/Fonts/Menlo.ttc",
        "/Library/Fonts/Courier New Bold.ttf" if bold else "/Library/Fonts/Courier New.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def pick_color(line: str) -> tuple:
    stripped = line.strip()
    if stripped.startswith("##") or stripped.startswith("##"):
        return HEADER_COLOR
    if "=" * 10 in stripped:
        return ACCENT_COLOR
    if stripped.startswith("🎵") or "TOP RECOMMENDATIONS" in stripped:
        return ACCENT_COLOR
    if stripped.startswith("#") and "Score:" not in stripped:
        return TITLE_COLOR
    if "Score:" in stripped:
        return SCORE_COLOR
    if stripped.startswith("•"):
        return BULLET_COLOR
    if stripped.startswith("by ") or stripped.startswith("─"):
        return (160, 160, 160)
    if "STANDARD TASTE" in stripped or "SYSTEM EVALUATION" in stripped or "ADVERSARIAL" in stripped:
        return HEADER_COLOR
    return FG_COLOR


def render_section(lines: list[str], label: str, out_path: str) -> None:
    font      = get_font(FONT_SIZE)
    font_bold = get_font(FONT_SIZE, bold=True)

    # Measure
    dummy = Image.new("RGB", (1, 1))
    dc    = ImageDraw.Draw(dummy)
    line_h = dc.textbbox((0, 0), "Ag", font=font)[3] + LINE_SPACING
    max_w  = max((dc.textbbox((0, 0), l, font=font)[2] for l in lines), default=400)

    img_w = max_w + PADDING * 2
    img_h = TOP_BAR_H + len(lines) * line_h + PADDING * 2

    img = Image.new("RGB", (img_w, img_h), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Top bar
    draw.rectangle([0, 0, img_w, TOP_BAR_H], fill=(50, 50, 50))
    for i, color in enumerate([(255, 95, 87), (255, 189, 46), (40, 200, 64)]):
        cx = 16 + i * 22
        draw.ellipse([cx - 7, TOP_BAR_H // 2 - 7, cx + 7, TOP_BAR_H // 2 + 7], fill=color)
    # window title
    title_font = get_font(FONT_SIZE - 2)
    tw = draw.textbbox((0, 0), label, font=title_font)[2]
    draw.text(((img_w - tw) // 2, (TOP_BAR_H - line_h + LINE_SPACING) // 2),
              label, font=title_font, fill=(180, 180, 180))

    # Text lines
    y = TOP_BAR_H + PADDING
    for line in lines:
        color = pick_color(line)
        draw.text((PADDING, y), line, font=font, fill=color)
        y += line_h

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, "PNG")
    print(f"  Saved: {out_path}")


def split_by_profile(raw_lines: list[str]) -> list[tuple[str, list[str]]]:
    """
    Split the full output into per-profile blocks.
    A new block starts at each '🎵  TOP RECOMMENDATIONS' banner.
    """
    sections: list[tuple[str, list[str]]] = []
    current_label = None
    current_lines: list[str] = []

    for line in raw_lines:
        if "TOP RECOMMENDATIONS" in line and "🎵" in line:
            if current_label is not None:
                sections.append((current_label, current_lines))
            # extract label between — and end
            try:
                current_label = line.split("—", 1)[1].strip().rstrip()
            except IndexError:
                current_label = line.strip()
            current_lines = [line]
        elif current_label is not None:
            current_lines.append(line)

    if current_label is not None:
        sections.append((current_label, current_lines))

    return sections


def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    result = subprocess.run(
        [sys.executable, "-m", "src.main"],
        capture_output=True, text=True, cwd=project_root
    )
    raw = result.stdout

    all_lines = raw.splitlines()
    sections  = split_by_profile(all_lines)

    print(f"Found {len(sections)} profile sections.")

    slug_map = {}
    for label, lines in sections:
        slug = label.lower().replace(" ", "_").replace("+", "plus").replace(",", "").replace("/", "_")
        # strip non-ascii
        slug = "".join(c for c in slug if c.isalnum() or c == "_")
        filename = f"profile_{slug}.png"
        out_path = os.path.join(project_root, "docs", "screenshots", filename)
        render_section(lines, label, out_path)
        slug_map[label] = f"docs/screenshots/{filename}"

    # Write a manifest for README use
    manifest_path = os.path.join(project_root, "docs", "screenshots", "manifest.txt")
    with open(manifest_path, "w") as f:
        for label, rel_path in slug_map.items():
            f.write(f"{label}|{rel_path}\n")
    print(f"\nManifest: {manifest_path}")
    return slug_map


if __name__ == "__main__":
    main()
