#!/usr/bin/env python3
"""Convert an image to ASCII art SVG using the portrait's character ramp.

Usage:
    python3 scripts/image_to_ascii.py input.png output.svg [--width 120] [--font-size 9] [--invert]
"""
import argparse
import base64
import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow required: pip install pillow")

# Same ramp as the portrait: quiet to loud
RAMP = [" ", ":", "+", "#", "@"]
# JetBrains Mono advance width ratio (0.6 em)
CHAR_ASPECT = 0.6
# Font files
FONT_DIR = Path(__file__).parent / "fonts"


def load_font_face(filename, weight):
    path = FONT_DIR / filename
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return (f"@font-face{{font-family:JBMono;font-style:normal;"
            f"font-weight:{weight};font-display:block;"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2')}}")


def font_css():
    return load_font_face("jbmono-400.woff2", 400) + load_font_face("jbmono-600.woff2", 600)


def image_to_ascii(img_path, width=120, invert=False):
    img = Image.open(img_path).convert("L")  # grayscale
    # Adjust height for character aspect ratio
    aspect = img.height / img.width
    height = int(width * aspect * CHAR_ASPECT)
    img = img.resize((width, height), Image.LANCZOS)
    pixels = img.load()

    if invert:
        ramp = list(reversed(RAMP))
    else:
        ramp = RAMP

    lines = []
    for y in range(height):
        line = []
        for x in range(width):
            val = pixels[x, y]
            idx = min(val * len(ramp) // 256, len(ramp) - 1)
            line.append(ramp[idx])
        lines.append("".join(line).rstrip())
    return lines, width, height


def escape_xml(text):
    return text.replace("&", "&").replace("<", "<").replace(">", ">")


def generate_svg(lines, char_w, char_h, font_size=9, line_height=11):
    # Calculate SVG dimensions
    svg_w = 40 + char_w * font_size * CHAR_ASPECT
    svg_h = 40 + char_h * line_height

    # Clip path reveal animation (same style as other SVGs)
    reveal_dur = 1.30
    clips = []
    text_elements = []

    for i, line in enumerate(lines):
        if not line:
            continue
        y = 20 + i * line_height
        line_w = len(line) * font_size * CHAR_ASPECT
        cid = f"ac{i}"
        delay = 0.10 + i * 0.02
        clips.append(
            f'<clipPath id="{cid}"><rect x="20" y="{y - font_size + 2}" '
            f'height="{line_height}" width="0"><animate attributeName="width" '
            f'from="0" to="{line_w:.1f}" begin="{delay:.2f}s" dur="{reveal_dur}s" '
            f'fill="freeze"/></rect></clipPath>'
        )
        safe = escape_xml(line)
        text_elements.append(
            f'<g clip-path="url(#{cid})"><text xml:space="preserve" '
            f'x="20" y="{y:.1f}" class="d-f" font-size="{font_size}">{safe}</text></g>'
        )

    style = (
        f"<style>{font_css()}"
        f".d-f{{fill:#6e7681}}.d-s{{stroke:#6e7681}}.e-f{{fill:#424a53}}"
        f".m-f{{fill:#8c959f}}.u-s{{stroke:#d8dee4}}.r{{stroke:#ffffff}}"
        f".w{{fill:#6e7681;opacity:.13}}"
        f"@media(prefers-color-scheme:dark){{"
        f".d-f{{fill:#c9d1d9}}.d-s{{stroke:#c9d1d9}}.e-f{{fill:#f0f6fc}}"
        f".m-f{{fill:#8b949e}}.u-s{{stroke:#30363d}}.r{{stroke:#0d1117}}"
        f".w{{fill:#c9d1d9;opacity:.16}}}}</style>"
    )

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w:.0f}" height="{svg_h:.0f}" '
        f'viewBox="0 0 {svg_w:.0f} {svg_h:.0f}" fill="none" '
        f'font-family="JBMono,ui-monospace,SFMono-Regular,Menlo,Consolas,\'Liberation Mono\',monospace">',
        style,
        *clips,
        *text_elements,
        "</svg>"
    ]
    return "".join(svg)


def main():
    parser = argparse.ArgumentParser(description="Convert image to ASCII SVG")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", help="Output SVG path")
    parser.add_argument("--width", type=int, default=120, help="ASCII width in characters")
    parser.add_argument("--font-size", type=int, default=9, help="Font size in px")
    parser.add_argument("--line-height", type=int, default=11, help="Line height in px")
    parser.add_argument("--invert", action="store_true", help="Invert ramp (dark bg)")
    args = parser.parse_args()

    lines, cw, ch = image_to_ascii(args.input, args.width, args.invert)
    svg = generate_svg(lines, cw, ch, args.font_size, args.line_height)

    Path(args.output).write_text(svg, encoding="utf-8")
    print(f"Generated {args.output}: {cw}x{ch} chars")


if __name__ == "__main__":
    main()