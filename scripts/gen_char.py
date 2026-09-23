#!/usr/bin/env python3
"""Render ONE glyph to a tight RGBA PNG (canvas width = glyph advance, so pasting adjacent reproduces layout).
Usage: gen_char.py <char> <font_path> <size> <r,g,b> <out.png>"""
import sys, math
from PIL import Image, ImageDraw, ImageFont

char, font_path, size, color_s, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
r, g, b = (int(c) for c in color_s.split(','))
f = ImageFont.truetype(font_path, size)
asc, desc = f.getmetrics()
adv = f.getlength(char)
w = max(1, int(math.ceil(adv)))
h = asc + desc
img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
if char.strip():
    d = ImageDraw.Draw(img)
    d.text((0, asc), char, font=f, fill=(r, g, b, 255))
img.save(out)
print(w)
