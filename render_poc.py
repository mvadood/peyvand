"""POC v2 renderer: background replacement, content-driven framing, animated graphics.

python render_poc.py            full render
python render_poc.py still T    one composited frame at edited time T -> work/still.jpg
"""
import json, math, os, re, subprocess, sys
from multiprocessing import Pool

import cv2
import numpy as np

from captions_test import CUES, MANUAL_CUTS

FF = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
D = os.path.expanduser("~/Downloads/2024-07-08--t10-46-31am")
SRC = {"m": f"{D}--6686af0927a13c251c09b980--mvadood.mov", "h": f"{D}--guest329206--hooman.mov"}
DIM = {"m": (2560, 1440), "h": (1920, 1080)}
ALPHA_SPLIT = 203.0
ALPHA = {"m": ("work/alpha_m.mp4", "work/alpha_m2.mp4"), "h": ("work/alpha_h.mp4", "work/alpha_h2.mp4")}
RANGE = (1.9, 401.3)
FPS, OW, OH, INTRO, DIP = 30, 1920, 1080, 4.0, 6
HOP = 0.1

# ---------------------------------------------------------------- shot plan (source time)
SHOTS = [
    (1.9, 9.1, "MW"), (9.1, 22.3, "MP"), (22.3, 27.8, "MW"), (27.8, 33.2, "MG:book"), (33.2, 40.96, "S"),
    (40.96, 58.2, "MC"), (58.2, 61.8, "MW"), (61.8, 72.8, "HW"), (72.8, 89.16, "HP"), (89.16, 101.6, "HC"),
    (101.6, 114.0, "S"), (114.0, 121.3, "MW"), (121.3, 128.4, "MC"), (128.4, 141.0, "MP"), (141.0, 149.7, "HW"),
    (149.7, 166.1, "HP"), (166.1, 181.6, "HW"), (181.6, 195.4, "HC"), (195.4, 207.0, "S"), (207.0, 214.0, "HG:sign1"),
    (214.0, 231.0, "HW"), (231.0, 248.5, "HP"), (248.5, 258.8, "S"), (258.8, 263.2, "HC"), (263.2, 280.0, "HW"),
    (280.0, 290.5, "HG:sign2"), (290.5, 303.0, "HC"), (303.0, 326.0, "HG:sign3"), (326.0, 343.7, "S"),
    (343.7, 360.2, "HP"), (360.2, 375.5, "HC"), (375.5, 386.7, "I"), (386.7, 393.0, "S"), (393.0, 401.3, "HW"),
]
SIGN3_LINES = [303.0, 306.6, 310.0, 313.2]  # source times each extra line appears
HEADLIGHTS_ON = 385.0

# framing: (zoom, cx, cy) in source fractions; P = push from W to C-ish
FRAME = {
    "m": {"W": (1.0, 0.5, 0.5), "C": (1.5, 0.5, 0.42), "P": ((1.0, 0.5, 0.5), (1.28, 0.5, 0.44)), "G": (1.05, 0.5, 0.5)},
    "h": {"W": (1.4, 0.515, 0.62), "C": (1.65, 0.515, 0.64), "P": ((1.4, 0.515, 0.62), (1.62, 0.515, 0.64)), "G": (1.45, 0.515, 0.62)},
}
BG_PARALLAX = 0.55
G_SHIFT = -0.21  # person moves left by this fraction of output width in graphic layout


def fr(t):
    return round(t * FPS) / FPS


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- edit decision list
def build_edl():
    state = np.load("work/state.npy")
    t = np.arange(len(state)) * HOP
    keep = (t >= RANGE[0]) & (t < RANGE[1])
    for a, b in MANUAL_CUTS:
        keep &= ~((t >= a) & (t < b))
    i = 0
    while i < len(state):
        if state[i] == "-":
            j = i
            while j < len(state) and state[j] == "-":
                j += 1
            if (j - i) * HOP >= 0.7:
                keep[i + 2 : j - 2] = False
            i = j
        else:
            i += 1
    intervals, i = [], 0
    while i < len(keep):
        if keep[i]:
            j = i
            while j < len(keep) and keep[j]:
                j += 1
            intervals.append((fr(i * HOP), fr(j * HOP)))
            i = j
        else:
            i += 1
    intervals = [(a, b) for a, b in intervals if b - a >= 0.2]

    segs = []
    for s0, s1, spec in SHOTS:
        for a, b in intervals:
            lo, hi = fr(max(a, s0)), fr(min(b, s1))
            if spec == "I" or spec.startswith("HG:sign3"):
                lo, hi = fr(max(a, s0)), fr(min(b, s1))
            for x0, x1 in ((lo, min(hi, ALPHA_SPLIT)), (max(lo, ALPHA_SPLIT), hi)):
                if x1 - x0 >= 2 / FPS:
                    segs.append([x0, x1, spec])
    # edited-time bookkeeping per shot, for push-ins and animations
    acc = INTRO
    shot_span = {}
    for s in segs:
        s.append(acc)
        key = (s[2], next(k for k, (a, b, sp) in enumerate(SHOTS) if a <= s[0] < b + 1e-6 and sp == s[2]))
        s.append(key[1])
        shot_span.setdefault(key[1], [acc, acc])
        acc += s[1] - s[0]
        shot_span[key[1]][1] = acc
    return segs, shot_span, acc


def src_to_edit(segs, ts, side):
    for a, b, spec, e0, _ in segs:
        if ts < a:
            return e0 if side == "start" else e0
        if ts <= b:
            return e0 + (ts - a)
    last = segs[-1]
    return last[3] + last[1] - last[0]


# ---------------------------------------------------------------- assets
_cache = {}


def asset(name):
    if name not in _cache:
        im = cv2.imread(f"assets/{name}.png", cv2.IMREAD_UNCHANGED)
        if im.shape[2] == 3:
            im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        else:
            im = cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA)
        _cache[name] = im
    return _cache[name]


def lut(r_gain, g_gain, b_gain, gamma=1.0, contrast=1.0, sat=1.0):
    x = np.arange(256) / 255.0
    x = x ** (1 / gamma)
    x = np.clip((x - 0.5) * contrast + 0.5, 0, 1)
    return np.stack([np.clip(x * g, 0, 1) for g in (r_gain, g_gain, b_gain)], 1), sat


GRADE = {"m": lut(1.0, 0.99, 0.98, gamma=1.0, contrast=1.05, sat=1.02), "h": lut(1.04, 1.0, 0.95, gamma=1.1, contrast=1.08, sat=1.08)}


def grade(img, p):
    table, sat = GRADE[p]
    out = np.empty_like(img)
    for c in range(3):
        out[..., c] = (table[:, c] * 255).astype(np.uint8)[img[..., c]]
    if sat != 1.0:
        g = out.mean(2, keepdims=True)
        out = np.clip(g + (out - g) * sat, 0, 255).astype(np.uint8)
    return out


def affine(p, z, cx, cy, ow, oh, clamp=True, dx=0.0):
    W, H = DIM[p]
    s = z * max(ow / W, oh / H)
    vw, vh = ow / s, oh / s
    X, Y = cx * W, cy * H
    if clamp:
        X = min(max(X, vw / 2), W - vw / 2)
    Y = min(max(Y, vh / 2), H - vh / 2)
    return np.float32([[s, 0, ow / 2 - s * X + dx], [0, s, oh / 2 - s * Y]]), (X, Y, s)


def compose_person(p, frame, alpha, z, cx, cy, ow, oh, dx=0.0):
    bg = asset("bg_milad" if p == "m" else "bg_hooman")
    M, (X, Y, s) = affine(p, z, cx, cy, ow, oh, clamp=(dx == 0), dx=dx)
    zb = 1 + (z - 1) * BG_PARALLAX
    Mb, _ = affine(p, zb, cx, cy, ow, oh, clamp=True)
    b = cv2.warpAffine(bg, Mb, (ow, oh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    f = cv2.warpAffine(grade(frame, p), M, (ow, oh), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    if p == "h":
        alpha = cv2.erode(alpha, np.ones((3, 3), np.uint8))
    a = cv2.warpAffine(alpha, M, (ow, oh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    a = cv2.GaussianBlur(a, (3, 3), 0).astype(np.float32)[..., None] / 255.0
    return (b * (1 - a) + f * a).astype(np.uint8)


def overlay(dst, img, cx, cy, scale=1.0, opacity=1.0):
    if scale != 1.0:
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    h, w = img.shape[:2]
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + w, dst.shape[1]), min(y0 + h, dst.shape[0])
    if xb <= xa or yb <= ya:
        return
    sub = img[ya - y0 : yb - y0, xa - x0 : xb - x0]
    a = sub[..., 3:4].astype(np.float32) / 255.0 * opacity
    dst[ya:yb, xa:xb] = (dst[ya:yb, xa:xb] * (1 - a) + sub[..., :3] * a).astype(np.uint8)


def round_mask(w, h, r):
    m = np.zeros((h, w), np.uint8)
    cv2.rectangle(m, (r, 0), (w - r, h), 255, -1)
    cv2.rectangle(m, (0, r), (w, h - r), 255, -1)
    for x, y in ((r, r), (w - r - 1, r), (r, h - r - 1), (w - r - 1, h - r - 1)):
        cv2.circle(m, (x, y), r, 255, -1, cv2.LINE_AA)
    return m.astype(np.float32)[..., None] / 255.0


PW, PH = 928, 1016
PANEL_MASK = round_mask(PW, PH, 28)


def canvas():
    y = np.linspace(0, 1, OH, dtype=np.float32)[:, None, None]
    return (np.array([12, 16, 22], np.float32) * (1 - y) + np.array([20, 26, 34], np.float32) * y).repeat(OW, 1).astype(np.uint8)


CANVAS = None


def split_frame(fm, am, fh, ah):
    global CANVAS
    if CANVAS is None:
        CANVAS = canvas()
    out = CANVAS.copy()
    for (p, f, a), x in ((("m", fm, am), 24), (("h", fh, ah), 968)):
        z, cx, cy = (1.3, 0.5, 0.42) if p == "m" else (1.4, 0.515, 0.62)
        panel = compose_person(p, f, a, z, cx, cy, PW, PH)
        region = out[32 : 32 + PH, x : x + PW]
        out[32 : 32 + PH, x : x + PW] = (region * (1 - PANEL_MASK) + panel * PANEL_MASK).astype(np.uint8)
    return out


# ---------------------------------------------------------------- frame rendering
def framing(p, kind, t_edit, span):
    F = FRAME[p][kind]
    if kind == "P":
        (z0, x0, y0), (z1, x1, y1) = F
        u = ease((t_edit - span[0]) / max(span[1] - span[0], 1e-3))
        return z0 + (z1 - z0) * u, x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
    return F


def graphic(out, name, t_src, t_edit, span):
    a_in = ease((t_edit - span[0]) / 0.45)
    a_out = ease((span[1] - t_edit) / 0.35)
    k = min(a_in, a_out)
    if name == "sign3":
        n = sum(1 for x in SIGN3_LINES if t_src >= x - 0.05) or 1
        img = asset(f"sign3_{n}")
        sc = 0.9
    elif name == "book":
        img, sc = asset("book_card"), 0.9
    else:
        img, sc = asset(name), 0.78
    cx = OW * 0.70 + (1 - a_in) * 260
    overlay(out, img, cx, OH * 0.44, sc, k)


def tunnel_frame(t_edit, t_src, span):
    scene, lights = asset("tunnel"), asset("tunnel_lights")
    u = ease((t_edit - span[0]) / max(span[1] - span[0], 1e-3))
    z = 1.0 + 0.14 * u
    M = np.float32([[z, 0, OW / 2 - z * OW / 2], [0, z, OH / 2 - z * OH * 0.42 - (1 - z) * 0]])
    M[1, 2] = OH * 0.42 - z * OH * 0.42
    img = scene.copy()
    k = ease((t_src - HEADLIGHTS_ON) / 0.6)
    if k > 0:
        a = lights[..., 3:4].astype(np.float32) / 255.0 * k
        img[..., :3] = np.clip(img[..., :3] * (1 - a) + lights[..., :3] * a, 0, 255).astype(np.uint8)
    return cv2.warpAffine(img[..., :3], M, (OW, OH), flags=cv2.INTER_CUBIC)


def reader(path, start, n, w, h, gray=False):
    cmd = [FF, "-v", "error", "-ss", f"{start:.4f}", "-i", path, "-frames:v", str(n), "-vf", f"scale={w}:{h}",
           "-f", "rawvideo", "-pix_fmt", "gray" if gray else "rgb24", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    size = w * h * (1 if gray else 3)
    for _ in range(n):
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        yield np.frombuffer(buf, np.uint8).reshape((h, w) if gray else (h, w, 3))
    proc.stdout.close(); proc.wait()


def open_person(p, a, n):
    W, H = DIM[p]
    part = 0 if a < ALPHA_SPLIT else 1
    at = a if part == 0 else a - ALPHA_SPLIT
    return zip(reader(SRC[p], a, n, W, H), reader(ALPHA[p][part], at, n, W, H, gray=True))


def render_segment(args):
    idx, (a, b, spec, e0, shot_idx), span, prev_spec, next_spec, out_path = args
    n = round((b - a) * FPS)
    writer = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS),
                               "-i", "-", "-c:v", "libx264", "-preset", "fast", "-crf", "13", "-pix_fmt", "yuv420p", out_path],
                              stdin=subprocess.PIPE)
    kind = spec.split(":")[0]
    gname = spec.split(":")[1] if ":" in spec else None
    if kind == "I":
        frames = ((None,) for _ in range(n))
    elif kind == "S":
        frames = ((x, y) for x, y in zip(open_person("m", a, n), open_person("h", a, n)))
    else:
        frames = ((x,) for x in open_person(kind[0].lower(), a, n))
    for i, fr_ in enumerate(frames):
        t_edit, t_src = e0 + i / FPS, a + i / FPS
        if kind == "I":
            out = tunnel_frame(t_edit, t_src, span)
        elif kind == "S":
            (fm, am), (fh, ah) = fr_
            out = split_frame(fm, am, fh, ah)
        else:
            p = kind[0].lower()
            (f, al), = fr_
            mode = kind[1]
            z, cx, cy = framing(p, mode, t_edit, span)
            out = compose_person(p, f, al, z, cx, cy, OW, OH, dx=G_SHIFT * OW if mode == "G" else 0.0)
            if gname:
                graphic(out, gname, t_src, t_edit, span)
        # dip to/from black around the tunnel interstitial
        k = 1.0
        if kind == "I" or (prev_spec == "I" and spec != "I"):
            k = min(k, (t_edit - span[0]) * FPS / DIP + 1 / DIP)
        if kind == "I":
            k = min(k, (span[1] - t_edit) * FPS / DIP - 1 / DIP)
        if k < 1.0:
            out = (out * max(k, 0.0)).astype(np.uint8)
        writer.stdin.write(np.ascontiguousarray(out).tobytes())
    writer.stdin.close(); writer.wait()
    return out_path


def intro_card(path):
    fm, am = next(open_person("m", 20, 1))
    fh, ah = next(open_person("h", 20, 1))
    bg = cv2.GaussianBlur(split_frame(fm, am, fh, ah), (0, 0), 28)
    bg = (bg * 0.55).astype(np.uint8)
    n = round(INTRO * FPS)
    writer = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS),
                               "-i", "-", "-c:v", "libx264", "-preset", "fast", "-crf", "13", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for i in range(n):
        t = i / FPS
        k = min(ease(t / 0.6), ease((INTRO - t) / 0.5))
        z = 1.0 + 0.04 * t / INTRO
        M = np.float32([[z, 0, OW / 2 * (1 - z)], [0, z, OH / 2 * (1 - z)]])
        writer.stdin.write((cv2.warpAffine(bg, M, (OW, OH)) * k).astype(np.uint8).tobytes())
    writer.stdin.close(); writer.wait()


def rtl(txt):
    """Wrap Persian text in RLM marks (after any leading {override} blocks) so libass keeps
    edge punctuation like « » ؟ : on the correct side."""
    if not re.search("[\u0600-\u06FF]", txt):
        return txt
    m = re.match(r"((?:\{[^}]*\})*)(.*)", txt, re.S)
    return m.group(1) + "\u200f" + m.group(2) + "\u200f"


# ---------------------------------------------------------------- captions / text (ASS)
def write_ass(segs, spans, total):
    def ts(x):
        h, x = divmod(max(x, 0), 3600); m, s = divmod(x, 60)
        return f"{int(h)}:{int(m):02d}:{s:05.2f}"

    ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 0", "",
           "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           "Style: Cap,SF Arabic,56,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,1,0,0,0,100,100,0,0,1,3.2,1.2,2,140,140,64,1",
           "Style: Name,SF Arabic,44,&H00FFFFFF,&H00FFFFFF,&H00101010,&H00000000,1,0,0,0,100,100,0,0,1,0,0,1,96,96,210,1",
           "Style: Tag,SF Arabic,32,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
           "Style: Title,DIN Alternate,120,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,2,0,1,0,0,5,0,0,0,1",
           "Style: Sub,SF Arabic,54,&H005AC8FF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1",
           "Style: Small,DIN Alternate,38,&H00B4B4B4,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,1,0,1,0,0,5,0,0,0,1",
           "Style: Card,DIN Alternate,40,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,1,0,1,0,0,7,0,0,0,1",
           "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]

    def ev(s, e, st, txt, layer=0):
        ass.append(f"Dialogue: {layer},{ts(s)},{ts(e)},{st},,0,0,0,,{rtl(txt)}")

    fade = r"{\fad(250,250)}"
    ev(0.3, INTRO - 0.3, "Title", r"{\fad(400,300)\pos(960,450)}ARE YOUR LIGHTS ON?")
    ev(0.7, INTRO - 0.3, "Sub", r"{\fad(400,300)\pos(960,590)}گفتگو درباره‌ی کتاب «آیا چراغ‌هات روشنه؟»")
    ev(1.0, INTRO - 0.3, "Small", r"{\fad(400,300)\pos(960,680)}DONALD C. GAUSE  ·  GERALD M. WEINBERG")

    for a, b, who, text in CUES:
        pieces = text.split("|")
        tot, t0 = sum(len(p) for p in pieces), a
        for p in pieces:
            t1 = t0 + (b - a) * len(p) / tot
            s, e = src_to_edit(segs, t0, "start"), src_to_edit(segs, t1, "end")
            if e - s > 0.25:
                ev(s, e, "Cap", p)
            t0 = t1

    # name lower-thirds with an amber accent bar, first full-frame appearance
    shown = set()
    for a, b, spec, e0, _ in segs:
        k = spec[0]
        if k in "MH" and k not in shown and b - a > 2.5:
            shown.add(k)
            nm = "میلاد" if k == "M" else "هومان"
            ev(e0 + 0.3, e0 + min(4.5, b - a - 0.2), "Name", r"{\fad(300,300)\1c&H005AC8FF&}▍{\1c&H00FFFFFF&}" + nm)
        if spec == "S":
            ev(e0, e0 + b - a, "Tag", r"{\pos(52,60)\bord2\3c&H000000&}میلاد", 1)
            ev(e0, e0 + b - a, "Tag", r"{\pos(996,60)\bord2\3c&H000000&}هومان", 1)
    # authors card during the author names
    s, e = src_to_edit(segs, 49.0, "start"), src_to_edit(segs, 58.0, "end")
    ev(s, e, "Card", r"{\fad(300,300)\pos(80,70)\bord0\shad0}{\c&H005AC8FF&}THE AUTHORS{\c&HFFFFFF&}\N{\fs52}Gerald M. Weinberg\N{\fs52}Donald C. Gause")
    open("work/poc.ass", "w").write("\n".join(ass) + "\n")


# ---------------------------------------------------------------- audio
def build_audio(segs, total):
    voice = ("highpass=f=85,lowpass=f=14000,afftdn=nf=-32:tn=1,"
             "equalizer=f=200:t=q:w=1:g=-2,equalizer=f=3200:t=q:w=1.2:g=2.5,deesser=i=0.35,"
             "acompressor=threshold=-24dB:ratio=3:attack=8:release=160:makeup=3,loudnorm=I=-19:TP=-3:LRA=8")
    subprocess.run([FF, "-v", "error", "-y", "-t", str(RANGE[1] + 1), "-i", SRC["m"], "-t", str(RANGE[1] + 1), "-i", SRC["h"],
                    "-filter_complex", f"[0:a]{voice}[a];[1:a]{voice}[b];[a][b]amix=inputs=2:normalize=0,aresample=48000[o]",
                    "-map", "[o]", "-c:a", "pcm_s16le", "work/mix.wav"], check=True)
    fc, parts = [], []
    for i, (a, b, spec, e0, _) in enumerate(segs):
        fc.append(f"[0:a]atrim={a:.4f}:{b:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={b-a-0.012:.4f}:d=0.012[s{i}]")
        parts.append(f"[s{i}]")
    fc.append(f"anullsrc=r=48000:cl=mono,atrim=0:{INTRO}[pre]")
    fc.append("[pre]" + "".join(parts) + f"concat=n={len(parts)+1}:v=0:a=1[cut]")
    open("work/afilter.txt", "w").write(";\n".join(fc))
    subprocess.run([FF, "-v", "error", "-y", "-i", "work/mix.wav", "-/filter_complex", "work/afilter.txt", "-map", "[cut]",
                    "-c:a", "pcm_s16le", "work/voice_cut.wav"], check=True)
    # music: intro bed, low bed under the tunnel reveal, outro swell; ducked under speech
    i0 = src_to_edit(segs, 375.5, "start"); i1 = src_to_edit(segs, 386.7, "end")
    vol = (f"volume='if(lt(t,{INTRO}),0.45,"
           f"if(lt(t,{INTRO+2.5}),0.45*(1-(t-{INTRO})/2.5),"
           f"if(between(t,{i0-1:.2f},{i1:.2f}),0.22*min(1,(t-{i0-1:.2f})/1.5),"
           f"if(gt(t,{total-8:.2f}),0.35*min(1,(t-{total-8:.2f})/3),0.0))))':eval=frame")
    fc = (f"[1:a]aloop=loop=-1:size=2e9,atrim=0:{total:.3f},{vol},afade=t=out:st={total-1.2:.3f}:d=1.2[mus];"
          f"[0:a]asplit[v1][v2];[mus][v2]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=500[duck];"
          f"[v1][duck]amix=inputs=2:normalize=0[o]")
    subprocess.run([FF, "-v", "error", "-y", "-i", "work/voice_cut.wav", "-i", "assets/music.wav", "-filter_complex", fc,
                    "-map", "[o]", "-ac", "2", "-c:a", "pcm_s16le", "work/premaster.wav"], check=True)
    m = subprocess.run([FF, "-hide_banner", "-i", "work/premaster.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    js = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=9:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}"
          f":measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run([FF, "-v", "error", "-y", "-i", "work/premaster.wav", "-af", ln + ",aresample=48000", "-c:a", "pcm_s16le",
                    "work/master.wav"], check=True)


# ---------------------------------------------------------------- main
if __name__ == "__main__":
    segs, spans, total = build_edl()
    if len(sys.argv) > 2 and sys.argv[1] == "still":
        T = float(sys.argv[2])
        for s in segs:
            if s[3] <= T < s[3] + s[1] - s[0]:
                a = s[0] + (T - s[3])
                one = [a, a + 1 / FPS, s[2], T, s[4]]
                idx = segs.index(s)
                render_segment((0, one, spans[s[4]], segs[idx - 1][2] if idx else None, None, "work/still.mp4"))
                subprocess.run([FF, "-v", "error", "-y", "-i", "work/still.mp4", "-frames:v", "1", "work/still.jpg"], check=True)
                print(s[2], f"src {a:.2f}")
                break
        sys.exit()

    os.makedirs("work/segs2", exist_ok=True)
    print(f"{len(segs)} segments, edited {total:.1f}s")
    jobs = []
    for i, s in enumerate(segs):
        prev = segs[i - 1][2] if i else None
        nxt = segs[i + 1][2] if i + 1 < len(segs) else None
        jobs.append((i, s, spans[s[4]], prev, nxt, f"work/segs2/{i:04d}.mp4"))
    intro_card("work/segs2/intro.mp4")
    with Pool(5) as pool:
        for k, _ in enumerate(pool.imap(render_segment, jobs)):
            if k % 20 == 0:
                print(f"  rendered {k}/{len(jobs)}", flush=True)
    with open("work/concat2.txt", "w") as f:
        f.write("file 'segs2/intro.mp4'\n")
        for j in jobs:
            f.write(f"file '{j[5][5:]}'\n")
    subprocess.run([FF, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "work/concat2.txt", "-c", "copy", "work/video_v2.mp4"], check=True)
    write_ass(segs, spans, total)
    build_audio(segs, total)
    subprocess.run([FF, "-v", "error", "-y", "-i", "work/video_v2.mp4", "-i", "work/master.wav",
                    "-vf", f"ass=work/poc.ass,noise=alls=3:allf=t,fade=out:st={total-0.8:.3f}:d=0.8",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", "-shortest", "renders/v2_poc.mp4"], check=True)
    print("wrote renders/v2_poc.mp4", f"{total:.1f}s")
