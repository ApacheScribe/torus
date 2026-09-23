#!/usr/bin/env python3
"""Assemble a text overlay by rendering each glyph in its own subprocess (sandbox kill budget ~7 glyphs/process).
Usage: gen_overlay2.py <name>
Writes /tmp/tov/<name>.png
"""
import subprocess, sys, os
from PIL import Image

SERIF = "/usr/share/fonts/dejavu/DejaVuSerif.ttf"
SERIF_I = "/usr/share/fonts/dejavu/DejaVuSerif-Italic.ttf"
SERIF_B = "/usr/share/fonts/dejavu/DejaVuSerif-Bold.ttf"
OUT = "/tmp/tov"
os.makedirs(OUT, exist_ok=True)
CHAR = "/tmp/gen_char.py"
TMP = "/tmp/tglyphs"

STYLES = {"serif": SERIF, "italic": SERIF_I, "bold": SERIF_B}

# name: list of (text, style, size, "r,g,b")
SPECS = {
    "title": [("The Torus, from a Flat Plane", "serif", 62, "255,255,255")],
    "rect":  [("a rectangle in the plane", "serif", 34, "255,255,255")],
    "cyl":   [("glue left", "serif", 34, "255,255,255"), (" \u2194 ", "serif", 34, "255,200,90"), ("right", "serif", 34, "255,255,255"), (" \u2192 ", "serif", 34, "255,200,90"), ("cylinder", "serif", 34, "255,255,255")],
    "tor":   [("glue top", "serif", 34, "255,255,255"), (" \u2194 ", "serif", 34, "120,220,160"), ("bottom", "serif", 34, "255,255,255"), (" \u2192 ", "serif", 34, "120,220,160"), ("torus", "serif", 34, "255,255,255")],
    "field": [("the grid", "serif", 34, "255,255,255"), (" \u2192 ", "serif", 34, "255,200,90"), ("a field of circles", "serif", 34, "255,255,255")],
    "map1":  [("T", "italic", 32, "255,255,255"), ("(u, v) = ((R + r cos v) cos u,", "serif", 32, "255,255,255")],
    "map2":  [("(R + r cos v) sin u, r sin v)", "serif", 32, "255,255,255")],
    "recap": [("Torus", "serif", 40, "255,255,255"), (" = ", "serif", 40, "255,255,255"), ("circle", "italic", 40, "255,200,90"), (" \u00d7 ", "serif", 40, "255,255,255"), ("circle", "italic", 40, "120,220,160")],
}

def glyph_png(ch, style, size, color, idx):
    path = f"{TMP}/{idx}.png"
    r = subprocess.run([sys.executable, CHAR, ch, STYLES[style], str(size), color, path],
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(path):
        raise RuntimeError(f"glyph fail {ch!r}: {r.stderr}")
    return path

def assemble(name):
    os.makedirs(TMP, exist_ok=True)
    segs = SPECS[name]
    # max height
    maxh = 0
    for text, style, size, color in segs:
        asc, desc = 0, 0
        # estimate height via a probe glyph
        import math
        from PIL import ImageFont as IF
        f = IF.truetype(STYLES[style], size)
        a, d = f.getmetrics()
        maxh = max(maxh, a + d)
    total_w = 0
    pieces = []
    idx = 0
    for text, style, size, color in segs:
        for ch in text:
            p = glyph_png(ch, style, size, color, idx)
            im = Image.open(p)
            pieces.append(im)
            total_w += im.width
            idx += 1
    canvas = Image.new("RGBA", (total_w, maxh), (0, 0, 0, 0))
    x = 0
    for im in pieces:
        canvas.paste(im, (x, 0), im)
        x += im.width
    out = f"{OUT}/{name}.png"
    canvas.save(out)
    print(f"saved {name} {canvas.size}", flush=True)

if __name__ == "__main__":
    assemble(sys.argv[1])
