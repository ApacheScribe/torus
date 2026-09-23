#!/usr/bin/env python3
"""3b1b-style: The Torus, from a Flat Cartesian Plane.
Morph: flat rectangle -> cylinder -> torus; grid becomes a field of circles.
Timeline driven by assets/timeline.json (written by sync.py from narration) or built-in defaults.
Every transition is a smoothstep with zero-velocity joints; all times are frame-quantized (t = fr/FPS)."""
import sys, math, os, json
from PIL import Image, ImageDraw

W, H, FPS = 960, 540, 24
BG = (18, 18, 18)
GRID = (45, 45, 50)
AXIS = (95, 95, 105)
RECT_FILL = (26, 34, 56)
AMBER = (255, 200, 90)
GREEN = (120, 220, 160)
BACK = (60, 80, 105)
FRONT = (150, 215, 255)

R, r = 2.2, 0.9
SCALE = 120.0
FOV = 2.2
NU, NV = 32, 16

# defaults (no narration): 26s
DEF_B = [2.2, 3.6, 6.4, 10.4, 14.4, 19.2, 23.0, 26.0]

def load_timeline(path):
    if os.path.exists(path):
        j = json.load(open(path))
        b = [0.0] + [float(x) for x in j["boundaries"]]
        b.append(float(j["duration"]))
        return b
    return [0.0] + DEF_B

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
B = load_timeline(os.path.join(ROOT, "assets/timeline.json"))
TOTAL = math.floor(B[-1] * FPS)

OV = os.path.join(ROOT, "assets/ov")
def load(name): return Image.open(f"{OV}/{name}.png")
TITLE, RECT, CYL, TOR, FIELD = load("title"), load("rect"), load("cyl"), load("tor"), load("field")
MAP1, MAP2, RECAP = load("map1"), load("map2"), load("recap")

def ease(t):
    t = 0.0 if t < 0 else (1.0 if t > 1 else t)
    return t * t * (3 - 2 * t)
def clamp01(t): return 0.0 if t < 0 else (1.0 if t > 1 else t)
def seg(t, t0, t1, a0, a1):
    """eased segment; a0==a1 gives constant (zero-velocity joints)."""
    if t1 <= t0: return a1
    return a0 + (a1 - a0) * ease(clamp01((t - t0) / (t1 - t0)))
def lerp3(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)

def flat_point(u, v, sf):
    return (u - math.pi, (v - 0.5) * sf, 0.0)

def cyl_point(u, v):
    return (R * math.cos(u), R * math.sin(u), (v - 0.5) * 2.0)

def torus_point(u, v):
    vv = 2 * math.pi * v
    return ((R + r * math.cos(vv)) * math.cos(u),
            (R + r * math.cos(vv)) * math.sin(u),
            r * math.sin(vv))

def morph(u, v, t_cyl, t_tor):
    sf = 1.0 + 1.8 * (1.0 - t_cyl)          # flat stage rectangle stretched for visibility
    p = lerp3(flat_point(u, v, sf), cyl_point(u, v), t_cyl)
    return lerp3(p, torus_point(u, v), t_tor)

def view_rot(p, elev, azim):
    x, y, z = p
    ca, sa = math.cos(azim), math.sin(azim)
    x, z = x * ca - z * sa, x * sa + z * ca
    ce, se = math.cos(elev), math.sin(elev)
    y, z = y * ce - z * se, y * se + z * ce
    return (x, y, z)

def project(p, elev, azim, dist):
    x, y, z = view_rot(p, elev, azim)
    f = FOV / (dist - z)
    return (W / 2 + x * f * SCALE, H / 2 - y * f * SCALE)

def paste_alpha(base, overlay, pos, alpha):
    a = clamp01(alpha)
    if a <= 0: return
    if a >= 1:
        base.paste(overlay, pos, overlay); return
    ov = overlay.copy()
    ov.putalpha(ov.getchannel("A").point(lambda v: int(v * a)))
    base.paste(ov, pos, ov)

def mix_col(c, a):
    return (int(c[0] + (BG[0] - c[0]) * (1 - a)), int(c[1] + (BG[1] - c[1]) * (1 - a)), int(c[2] + (BG[2] - c[2]) * (1 - a)))

def draw_plane_grid(d, elev, azim, dist, alpha):
    if alpha <= 0: return
    gc = mix_col(GRID, alpha); ax = mix_col(AXIS, alpha)
    for i in range(-4, 5):
        d.line([project((i, -2, 0), elev, azim, dist), project((i, 2, 0), elev, azim, dist)],
               fill=ax if i == 0 else gc, width=2 if i == 0 else 1)
    for j in range(-2, 3):
        d.line([project((-4, j, 0), elev, azim, dist), project((4, j, 0), elev, azim, dist)],
               fill=ax if j == 0 else gc, width=2 if j == 0 else 1)

def draw_shape(d, t_cyl, t_tor, elev, azim, dist):
    for i in range(NU + 1):
        u = 2 * math.pi * i / NU
        p3 = [view_rot(morph(u, j / NV, t_cyl, t_tor), elev, azim) for j in range(NV + 1)]
        p2 = [(W / 2 + x * FOV / (dist - z) * SCALE, H / 2 - y * FOV / (dist - z) * SCALE) for (x, y, z) in p3]
        draw_curve(d, p3, p2)
    for j in range(NV + 1):
        v = j / NV
        p3 = [view_rot(morph(i / NU * 2 * math.pi, v, t_cyl, t_tor), elev, azim) for i in range(NU + 1)]
        p2 = [(W / 2 + x * FOV / (dist - z) * SCALE, H / 2 - y * FOV / (dist - z) * SCALE) for (x, y, z) in p3]
        draw_curve(d, p3, p2)

def draw_curve(d, p3, p2):
    for i in range(len(p3) - 1):
        z = (p3[i][2] + p3[i + 1][2]) / 2.0
        d.line([p2[i], p2[i + 1]], fill=FRONT if z > 0 else BACK, width=2)

def draw_rect(d, t_cyl, t_tor, elev, azim, dist, alpha):
    if alpha <= 0: return
    S = 24
    corners = [project(morph(0.0, 0.0, t_cyl, t_tor), elev, azim, dist),
               project(morph(2 * math.pi, 0.0, t_cyl, t_tor), elev, azim, dist),
               project(morph(2 * math.pi, 1.0, t_cyl, t_tor), elev, azim, dist),
               project(morph(0.0, 1.0, t_cyl, t_tor), elev, azim, dist)]
    d.polygon(corners, fill=mix_col(RECT_FILL, alpha))
    am, gr = mix_col(AMBER, alpha), mix_col(GREEN, alpha)
    # left/right edges (amber, glued first)
    for k in (0.0, 1.0):
        u = k * 2 * math.pi
        for j in range(S):
            v0, v1 = j / S, (j + 1) / S
            d.line([project(morph(u, v0, t_cyl, t_tor), elev, azim, dist),
                    project(morph(u, v1, t_cyl, t_tor), elev, azim, dist)], fill=am, width=3)
    # top/bottom edges (green, glued second)
    for k in (0.0, 1.0):
        v = k
        for i in range(S):
            u0, u1 = i / S * 2 * math.pi, (i + 1) / S * 2 * math.pi
            d.line([project(morph(u0, v, t_cyl, t_tor), elev, azim, dist),
                    project(morph(u1, v, t_cyl, t_tor), elev, azim, dist)], fill=gr, width=3)

def camera(t):
    b1, b2, b3, b4, b5, b6, b7 = B[1:8]
    # azim: continuous piecewise; each eased joint has zero velocity
    if t < b3:   azim = seg(t, 0.0, b3, 0.0, 0.10)
    elif t < b4: azim = seg(t, b3, b4, 0.10, -0.65)
    elif t < b5: azim = -0.65
    elif t < b6: azim = seg(t, b4, b5, -0.65, -1.20) if False else seg(t, b5, b6, -0.65, -1.20)
    else:        azim = seg(t, b6, b7, -1.20, -1.45)
    if t >= b5 and t < b6:
        azim = seg(t, b5, b6, -0.65, -1.20)
    # elev: top-down -> 3/4 view over the cylinder phase
    elev = 1.05 if t < b3 else (0.42 if t >= b4 else seg(t, b3, b4, 1.05, 0.42))
    # dist: zoomed-in on the rectangle early, pull back while curling
    dist = 4.6 if t < b3 else (7.0 if t >= b4 else seg(t, b3, b4, 4.6, 7.0))
    return elev, azim, dist

def state(t):
    b1, b2, b3, b4, b5, b6, b7 = B[1:8]
    t_cyl = 0.0 if t < b3 else (1.0 if t >= b4 else seg(t, b3, b4, 0.0, 1.0))
    t_tor = 0.0 if t < b4 else (1.0 if t >= b5 else seg(t, b4, b5, 0.0, 1.0))
    grid_a = 1.0 if t < b4 else max(0.0, 1.0 - ease((t - b4) / 1.2))
    rect_a = clamp01(ease((t - b1) / 0.6)) * clamp01(1.0 - ease((t - b5) / 0.5))
    return t_cyl, t_tor, grid_a, rect_a

def render_frame(fr):
    t = fr / FPS
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    elev, azim, dist = camera(t)
    t_cyl, t_tor, grid_a, rect_a = state(t)
    draw_plane_grid(d, elev, azim, dist, grid_a)
    draw_rect(d, t_cyl, t_tor, elev, azim, dist, rect_a)
    draw_shape(d, t_cyl, t_tor, elev, azim, dist)
    # labels: fade in 0.35s at step start, out 0.35s at next step (last label holds)
    def lab(bt, bt1):
        a = ease(clamp01((t - bt) / 0.35))
        if bt1 is not None:
            a *= 1.0 - ease(clamp01((t - bt1) / 0.35))
        return a
    b = B
    paste_alpha(img, TITLE, ((W - TITLE.width) // 2, 36), lab(0.0, None) * 0.95)
    paste_alpha(img, RECT, ((W - RECT.width) // 2, 468), lab(b[2], b[3]))
    paste_alpha(img, CYL, ((W - CYL.width) // 2, 468), lab(b[3], b[4]))
    paste_alpha(img, TOR, ((W - TOR.width) // 2, 468), lab(b[4], b[5]))
    paste_alpha(img, FIELD, ((W - FIELD.width) // 2, 468), lab(b[5], b[6]))
    paste_alpha(img, MAP1, ((W - MAP1.width) // 2, 438), lab(b[6], b[7]))
    paste_alpha(img, MAP2, ((W - MAP2.width) // 2, 476), lab(b[6], b[7]))
    paste_alpha(img, RECAP, ((W - RECAP.width) // 2, 250), lab(b[7], None))
    return img

def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end = int(sys.argv[2]) if len(sys.argv) > 2 else TOTAL
    outdir = sys.argv[3] if len(sys.argv) > 3 else "/tmp/tb_frames"
    os.makedirs(outdir, exist_ok=True)
    for fr in range(start, min(end, TOTAL)):
        render_frame(fr).save(f"{outdir}/f{fr:04d}.ppm")
    print(f"frames {start}-{min(end, TOTAL)} of {TOTAL} done", flush=True)

if __name__ == "__main__":
    main()