#!/usr/bin/env python3
"""Convert pre-made ASCII art (text file) to animated SVG.

Usage:
    python3 scripts/ascii_to_svg.py input.txt output.svg [--font-size 9] [--line-height 11]
"""
import argparse
import base64
import os
import sys
from pathlib import Path

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


def escape_xml(text):
    return text.replace("&", "&").replace("<", "<").replace(">", ">")


def generate_svg(lines, font_size=9, line_height=11):
    # Calculate dimensions
    max_len = max(len(line) for line in lines) if lines else 0
    # JetBrains Mono advance width ~0.6em
    char_w = font_size * 0.6
    svg_w = 40 + max_len * char_w
    svg_h = 40 + len(lines) * line_height

    reveal_dur = 1.30
    clips = []
    text_elements = []

    for i, line in enumerate(lines):
        if not line:
            continue
        y = 20 + i * line_height
        line_w = len(line) * char_w
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
    parser = argparse.ArgumentParser(description="Convert ASCII text file to animated SVG")
    parser.add_argument("input", help="Input text file path")
    parser.add_argument("output", help="Output SVG path")
    parser.add_argument("--font-size", type=int, default=9, help="Font size in px")
    parser.add_argument("--line-height", type=int, default=11, help="Line height in px")
    args = parser.parse_args()

    lines = Path(args.input).read_text(encoding="utf-8").splitlines()
    # Preserve trailing spaces by not stripping
    svg = generate_svg(lines, args.font_size, args.line_height)

    Path(args.output).write_text(svg, encoding="utf-8")
    print(f"Generated {args.output}: {len(lines)} lines, max width {max(len(l) for l in lines) if lines else 0}")


if __name__ == "__main__":
    main()