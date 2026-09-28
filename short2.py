"""Parking short v2 — illustration-led vertical edit using the Peyvand brand kit.

Every visual is an event tied to the spoken words (source time), so cuts land on words.
Transitions are soft dissolves; illustrations move with slow Ken Burns; speakers appear
briefly in the reading room and otherwise as a small bubble.

python short2.py               render renders/shorts/parking_v2.mp4
python short2.py still T       one frame at edited time T (no captions) -> work/s2_still.jpg
"""
import json, os, subprocess, sys
from multiprocessing import Pool

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import render_poc as R
from shorts import open_person
from shorts_cues import CLIPS

FF, FPS, HOP = R.FF, 30, 0.1
OW, OH = 1080, 1920
XF = 0.36  # dissolve length, seconds
BR = "assets/episodes/01/broll"
FONT = "assets/branding/layout-v2/fonts/Vazirmatn-Bold.ttf"
FONTDIR = "assets/branding/layout-v2/fonts"
NAVY, NAVY_DEEP, INK, GREY, AMBER = (22, 35, 59), (11, 18, 32), (21, 24, 27), (233, 236, 239), (242, 184, 75)
PLATES = {"m": "assets/branding/backgrounds/milad-reading-room-v1.png",
          "h": "assets/branding/backgrounds/hooman-reading-room-v1.png"}
PLATE_X0 = {"m": 300, "h": 657}  # left edge of the 9:16 slice taken from each 1672x941 plate
ANIM = "assets/branding/animation/peyvand-intro-vertical-dark.mp4"
SIGNATURE = "assets/branding/animation/audio/peyvand-sonic-signature.wav"
MUSIC = "assets/branding/music-v1/wav/peyvand-{}-v1.wav"
LOGO = "assets/branding/logo-kit/png/peyvand-logo-light-ink-1086.png"
STROKES = {"l": "assets/branding/derived/stroke-left-light.png", "r": "assets/branding/derived/stroke-right-light.png"}
CLIP = CLIPS["parking"]
END_DUR = 4.4
OUT = "renders/shorts/parking_v2.mp4"

# ---------------------------------------------------------------- the edit (source times)
# (start, end, kind, arg, bubble)   img arg: (name, zoom_from, zoom_to, centre_from, centre_to)
EVENTS = [
    (1748.60, 1752.20, "img", ("b08_president", 1.12, 1.03, (0.52, 0.56), (0.5, 0.52)), None),
    (1752.20, 1754.74, "book", None, ("m", 1480)),
    (1754.74, 1765.60, "quote", None, ("m", 1480)),
    (1765.60, 1768.80, "spk", "m", "h"),
    (1773.30, 1777.72, "spk", "h", None),
    (1777.72, 1781.42, "img", ("b02_university", 1.00, 1.08, (0.5, 0.62), (0.5, 0.48)), "h"),
    (1781.42, 1791.74, "img", ("b03_full_lot", 1.14, 1.00, (0.5, 0.5), (0.5, 0.5)), "h"),
    (1791.74, 1799.74, "img", ("b04_ignored_door", 1.00, 1.12, (0.5, 0.62), (0.5, 0.64)), "h"),
    (1799.74, 1806.22, "spk", "h", "m"),
    (1806.22, 1809.72, "img", ("b05_predawn_heist", 1.00, 1.07, (0.44, 0.56), (0.54, 0.56)), "h"),
    (1809.72, 1812.22, "img", ("b01_reserved_dawn", 1.10, 1.02, (0.38, 0.72), (0.45, 0.62)), "h"),
    (1812.22, 1815.40, "img", ("b06_ticket", 1.00, 1.08, (0.42, 0.62), (0.4, 0.6)), "h"),
    (1815.40, 1821.96, "img", ("b07_jar", 1.00, 1.10, (0.5, 0.72), (0.5, 0.74)), "h"),
    (1821.96, 1827.40, "img", ("b08_president", 1.00, 1.09, (0.5, 0.5), (0.44, 0.56)), "h"),
    (1827.40, 1832.00, "img", ("b09_new_garage", 1.07, 1.00, (0.62, 0.55), (0.5, 0.5)), "h"),
    (1832.00, 1837.86, "spk", "h", "m"),
    (1837.86, 1849.20, "lesson", None, "h"),
]
HOOK = ("اگه مسئله‌ی اونا نیست،", "مسئله‌ی اونا کنش!")
QUOTE_LINES = [(1754.74, "اگه مسئله،", False), (1756.98, "مسئله‌ی کسی نیست", False), (1759.18, "که باید حلش کنه،", False),
               (1760.44, "تبدیلش کن", True), (1761.58, "به مسئله‌ی اون آدم", True), (1763.44, "تا مجبور شه حلش کنه.", False)]
LESSON = dict(title=1837.86, symbol=1840.94, solver=1842.48, sufferer=1844.30, diff=1847.72)
CTA = ("قسمت کامل این گفتگو در یوتیوب", "youtu.be/peyvand-ep01")  # placeholder link
NAMES = {"m": "میلاد", "h": "هومان"}


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- timeline
def build():
    state = np.load("work/state.npy")
    t = np.arange(len(state)) * HOP
    keep = np.zeros(len(state), bool)
    for a, b in CLIP["ranges"]:
        keep |= (t >= a) & (t < b)
    i = 0
    while i < len(state):  # gentle: only pauses >= 0.6s, shortened to ~0.4s
        if state[i] == "-" and keep[i]:
            j = i
            while j < len(state) and state[j] == "-":
                j += 1
            if (j - i) * HOP >= 0.6:
                keep[i + 2 : j - 2] = False
            i = j
        else:
            i += 1
    segs, i, acc = [], 0, 0.0
    while i < len(keep):
        if keep[i]:
            j = i
            while j < len(keep) and keep[j]:
                j += 1
            a, b = R.fr(i * HOP), R.fr(j * HOP)
            segs.append((a, b, acc))
            acc += b - a
            i = j
        else:
            i += 1
    return segs, acc


def to_edit(segs, ts):
    for a, b, e0 in segs:
        if ts < a:
            return e0
        if ts <= b:
            return e0 + ts - a
    a, b, e0 = segs[-1]
    return e0 + b - a


def timeline():
    segs, speech = build()
    evs = []
    for s0, s1, kind, arg, bub in EVENTS:
        evs.append(dict(kind=kind, arg=arg, bubble=bub, s0=s0, s1=s1, e0=to_edit(segs, s0)))
    for k, ev in enumerate(evs):
        ev["e1"] = evs[k + 1]["e0"] if k + 1 < len(evs) else speech
    evs.append(dict(kind="end", arg=None, bubble=None, s0=None, s1=None, e0=speech, e1=speech + END_DUR))
    return segs, speech, evs


# ---------------------------------------------------------------- cached assets
_C = {}


def rgb(path):
    if path not in _C:
        _C[path] = cv2.cvtColor(cv2.imread(path, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
    return _C[path]


def rgba(path):
    if path not in _C:
        _C[path] = cv2.cvtColor(cv2.imread(path, cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA)
    return _C[path]


def font(size):
    key = ("font", size)
    if key not in _C:
        _C[key] = ImageFont.truetype(FONT, size, layout_engine=ImageFont.Layout.RAQM)
    return _C[key]


def text_img(s, size, color):
    """Persian (or Latin) text rendered once to a tight RGBA array."""
    key = ("txt", s, size, color)
    if key not in _C:
        f = font(size)
        d = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
        b = d.textbbox((0, 0), s, font=f, direction="rtl", language="fa")
        w, h = b[2] - b[0] + 20, b[3] - b[1] + 20
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((10 - b[0], 10 - b[1]), s, font=f, fill=color + (255,), direction="rtl", language="fa")
        _C[key] = np.array(im)
    return _C[key]


def gradient(top, bottom):
    key = ("grad", top, bottom)
    if key not in _C:
        y = np.linspace(0, 1, OH, dtype=np.float32)[:, None, None]
        _C[key] = (np.array(top, np.float32) * (1 - y) + np.array(bottom, np.float32) * y).repeat(OW, 1)
    return _C[key].copy()


def paste(dst, src, cx, cy, opacity=1.0, scale=1.0):
    """Alpha-composite an RGBA array onto a float RGB frame, centred at (cx, cy)."""
    if opacity <= 0:
        return
    if scale != 1.0:
        src = cv2.resize(src, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
    h, w = src.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + w, OW), min(y0 + h, OH)
    if xb <= xa or yb <= ya:
        return
    s = src[ya - y0 : yb - y0, xa - x0 : xb - x0].astype(np.float32)
    a = s[..., 3:4] / 255.0 * opacity
    dst[ya:yb, xa:xb] = dst[ya:yb, xa:xb] * (1 - a) + s[..., :3] * a


# ---------------------------------------------------------------- visuals
def ken_burns(arg, u):
    name, z0, z1, c0, c1 = arg
    img = rgb(f"{BR}/{name}.png")
    H, W = img.shape[:2]
    e = ease(u) * 0.85 + u * 0.15  # mostly eased, never fully stopped
    z = z0 + (z1 - z0) * e
    cx = (c0[0] + (c1[0] - c0[0]) * e) * W
    cy = (c0[1] + (c1[1] - c0[1]) * e) * H
    s = z * OW / W
    vw, vh = OW / s, OH / s
    cx = min(max(cx, vw / 2), W - vw / 2)
    cy = min(max(cy, vh / 2), H - vh / 2)
    M = np.float32([[s, 0, OW / 2 - s * cx], [0, s, OH / 2 - s * cy]])
    return cv2.warpAffine(img, M, (OW, OH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)


def plate(p):
    key = ("plate", p)
    if key not in _C:
        img = rgb(PLATES[p])
        w = int(img.shape[0] * 9 / 16)
        sl = img[:, PLATE_X0[p] : PLATE_X0[p] + w]
        big = cv2.resize(sl, (int(OW * 1.1), int(OH * 1.1)), interpolation=cv2.INTER_CUBIC).astype(np.float32)
        big = cv2.GaussianBlur(big, (0, 0), 7)  # lens depth of field; also hides the upscale
        big = big * 0.88  # push the room back a little
        _C[key] = big
    return _C[key]


# per speaker: zoom from/to, source face x, target face height in the output, colour gains, relight strength
SPK = {"m": dict(z=(1.00, 1.05), fx=0.50, fy=0.42, face_out=0.42, gain=(1.03, 1.0, 0.95), light=0.07),
       "h": dict(z=(1.30, 1.36), fx=0.515, fy=0.60, face_out=0.45, gain=(1.06, 1.01, 0.93), light=0.08)}


def speaker(p, frame, alpha, u):
    c = SPK[p]
    W, H = R.DIM[p]
    z = c["z"][0] + (c["z"][1] - c["z"][0]) * ease(u)
    s = z * OH / H
    X = c["fx"] * W
    Y = c["fy"] * H - (c["face_out"] - 0.5) * OH / s  # place the face at face_out of the frame height
    Y = max(Y, OH / s / 2)  # never above the top of the source
    M = np.float32([[s, 0, OW / 2 - s * X], [0, s, OH / 2 - s * Y]])
    fg = cv2.warpAffine(frame, M, (OW, OH), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
    al = alpha
    if p == "h":
        al = cv2.erode(al, np.ones((3, 3), np.uint8))
    a = cv2.warpAffine(al, M, (OW, OH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    a = cv2.GaussianBlur(a.astype(np.float32) / 255.0, (0, 0), 1.3)
    # background: the reading-room slice, moving at half the speed of the person (parallax)
    big = plate(p)
    zb = 1.0 + (z / c["z"][0] - 1.0) * 0.5
    Mb = np.float32([[zb, 0, OW / 2 - zb * big.shape[1] / 2], [0, zb, OH / 2 - zb * big.shape[0] / 2]])
    bg = cv2.warpAffine(big, Mb, (OW, OH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    # edge decontamination: replace fringe colour with colour propagated from the person's interior
    inner = (a > 0.96).astype(np.float32)
    num = cv2.GaussianBlur(fg * inner[..., None], (0, 0), 5)
    den = cv2.GaussianBlur(inner, (0, 0), 5)[..., None] + 1e-4
    fill = num / den
    edge = ((a > 0.02) & (a < 0.96))[..., None]
    fg = np.where(edge, 0.3 * fg + 0.7 * fill, fg)
    # match the room: warm white balance + light from the window side (left)
    fg = fg * np.array(c["gain"], np.float32)
    ramp = np.linspace(1 + c["light"], 1 - c["light"], OW, dtype=np.float32)[None, :, None]
    fg = fg * ramp
    # light wrap: let the blurred room bleed onto the person's edges
    wrap = a * (1 - cv2.GaussianBlur(a, (0, 0), 9))
    bgb = cv2.GaussianBlur(bg, (0, 0), 16)
    k = np.clip(wrap * 1.1, 0, 0.55)[..., None]
    fg = fg * (1 - k) + bgb * k
    out = bg * (1 - a[..., None]) + fg * a[..., None]
    # hide where the webcam frame ends below the torso
    yy = np.linspace(0, 1, OH, dtype=np.float32)
    shade = 1 - 0.92 * np.clip((yy - 0.80) / 0.2, 0, 1) ** 1.3
    return out * shade[:, None, None]


def book(u_in):
    out = gradient(NAVY, NAVY_DEEP)
    card = rgba("assets/book_card.png")
    k = ease(u_in / 0.5)
    paste(out, card, OW / 2 + 20, OH * 0.36 + (1 - k) * 40, opacity=k, scale=1.0 + 0.03 * u_in)
    return out


def quote(te, segs):
    out = gradient(NAVY, NAVY_DEEP)
    paste(out, rgba(STROKES["l"]), OW * 0.78, OH * 0.30, opacity=0.06, scale=1.5)
    hdr = text_img("یک جمله از کتاب", 40, (150, 165, 190))
    paste(out, hdr, 960 - hdr.shape[1] / 2, 440)
    y, shown = 520, 0
    for ts, line, accent in QUOTE_LINES:
        t0 = to_edit(segs, ts) - 0.1
        k = ease((te - t0) / 0.3)
        im = text_img(line, 78, AMBER if accent else (255, 255, 255))
        if k > 0:
            paste(out, im, 960 - im.shape[1] / 2, y + im.shape[0] / 2 + (1 - k) * 18, opacity=k)
            shown = y + im.shape[0]
        y += 110
    if shown:
        out[500 : int(shown), 986:994] = np.array(AMBER, np.float32)
    return out


def lesson(te, segs):
    L = {k: to_edit(segs, v) for k, v in LESSON.items()}
    out = gradient(NAVY, NAVY_DEEP)
    title = text_img("اکثر مشکلاتی که حل نمی‌شن…", 70, (255, 255, 255))
    paste(out, title, OW / 2, 400, opacity=ease((te - L["title"]) / 0.35))
    k_sym = ease((te - L["symbol"] + 0.2) / 0.5)
    split = ease((te - L["solver"] + 0.1) / 0.9)
    for side, img in (("l", rgba(STROKES["l"])), ("r", rgba(STROKES["r"]))):
        dx = (-1 if side == "l" else 1) * 190 * split
        dy = (-1 if side == "l" else 1) * 40 * split
        paste(out, img, OW / 2 + dx, 930 + dy, opacity=k_sym, scale=0.56)
    lab_r = text_img("کسی که می‌تونه حلش کنه", 42, GREY)
    lab_l = text_img("کسی که تجربه‌ش می‌کنه", 42, GREY)
    paste(out, lab_r, 790, 1360, opacity=ease((te - L["solver"]) / 0.35))
    paste(out, lab_l, 290, 1360, opacity=ease((te - L["sufferer"]) / 0.35))
    kd = ease((te - L["diff"] + 0.1) / 0.35)
    if kd > 0:
        out[1010:1300, 537:543] = out[1010:1300, 537:543] * (1 - kd) + np.array(AMBER, np.float32) * kd
        diff = text_img("فرق دارن", 96, AMBER)
        paste(out, diff, OW / 2, 1520 + (1 - kd) * 16, opacity=kd)
    return out


def end_card(t_rel, anim_frame):
    out = np.empty((OH, OW, 3), np.float32)
    out[:] = anim_frame[4, 4].astype(np.float32) if anim_frame is not None else np.array(INK, np.float32)
    if anim_frame is not None:
        small = cv2.resize(anim_frame, (648, 1152), interpolation=cv2.INTER_AREA).astype(np.float32)
        out[820 - 576 : 820 + 576, 216 : 216 + 648] = small
    return out


def draw(ev, te, ts, frames, segs):
    u = (te - ev["e0"]) / max(ev["e1"] - ev["e0"], 1e-3)
    k = ev["kind"]
    if k == "img":
        return ken_burns(ev["arg"], u)
    if k == "spk":
        f, a = frames[ev["arg"]]
        return speaker(ev["arg"], f, a, u)
    if k == "book":
        return book(te - ev["e0"])
    if k == "quote":
        return quote(te, segs)
    if k == "lesson":
        return lesson(te, segs)
    if k == "end":
        return end_card(te - ev["e0"], frames.get("anim"))
    raise ValueError(k)


# ---------------------------------------------------------------- overlays
BUB = dict(cx=190, cy=1150, r=112)
BUB_CROP = {"m": (0.5, 0.42, 720), "h": (0.515, 0.64, 520)}  # face centre (fractions) and square size in source px


def bubble_img(p, frame, alpha):
    fx, fy, size = BUB_CROP[p]
    W, H = R.DIM[p]
    x0, y0 = int(fx * W - size / 2), int(fy * H - size / 2)
    x0, y0 = min(max(x0, 0), W - size), min(max(y0, 0), H - size)
    d = BUB["r"] * 2
    f = cv2.resize(frame[y0 : y0 + size, x0 : x0 + size], (d, d), interpolation=cv2.INTER_AREA).astype(np.float32)
    a = cv2.resize(alpha[y0 : y0 + size, x0 : x0 + size], (d, d), interpolation=cv2.INTER_AREA).astype(np.float32)[..., None] / 255
    yy, xx = np.mgrid[0:d, 0:d].astype(np.float32)
    rr = np.sqrt((xx - d / 2) ** 2 + (yy - d / 2) ** 2) / (d / 2)
    bg = (np.array(NAVY, np.float32) * (1 - rr[..., None] * 0.5) + np.array(NAVY_DEEP, np.float32) * rr[..., None] * 0.5)
    img = bg * (1 - a) + f * a * np.array(SPK[p]["gain"], np.float32)
    mask = np.clip((1 - rr) * d / 2, 0, 1)
    return img, mask


def bub_key(b):
    return None if b is None else (b if isinstance(b, tuple) else (b, BUB["cy"]))


def overlay_bubble(out, key, frames, opacity):
    p, cy = key
    if opacity <= 0 or p not in frames:
        return
    img, mask = bubble_img(p, *frames[p])
    d = BUB["r"] * 2
    x0, y0 = BUB["cx"] - BUB["r"], cy - BUB["r"]
    # soft shadow + ring
    sh = cv2.GaussianBlur(mask, (0, 0), 8)
    pad = out[y0 + 8 : y0 + 8 + d, x0 : x0 + d]
    out[y0 + 8 : y0 + 8 + d, x0 : x0 + d] = pad * (1 - 0.45 * sh[..., None] * opacity)
    yy, xx = np.mgrid[0:d + 12, 0:d + 12].astype(np.float32)
    rr = np.sqrt((xx - (d + 12) / 2) ** 2 + (yy - (d + 12) / 2) ** 2)
    ring = np.clip(BUB["r"] + 5 - rr, 0, 1) * np.clip(rr - BUB["r"] + 1, 0, 1)
    reg = out[y0 - 6 : y0 + d + 6, x0 - 6 : x0 + d + 6]
    out[y0 - 6 : y0 + d + 6, x0 - 6 : x0 + d + 6] = reg * (1 - ring[..., None] * opacity) + np.array(GREY, np.float32) * ring[..., None] * opacity
    m = mask[..., None] * opacity
    out[y0 : y0 + d, x0 : x0 + d] = out[y0 : y0 + d, x0 : x0 + d] * (1 - m) + img * m


def scrims(out, kind):
    if kind == "end":
        return out
    yy = np.linspace(0, 1, OH, dtype=np.float32)
    k_top = np.clip(1 - yy / 0.16, 0, 1) ** 1.5 * 0.55
    k_bot = np.clip((yy - 0.62) / 0.38, 0, 1) ** 1.4 * 0.55
    k = (k_top + k_bot)[:, None, None]
    return out * (1 - k)


def watermark(out, opacity=0.9):
    logo = rgba(LOGO)
    paste(out, logo, OW / 2, 108, opacity=opacity, scale=118 / logo.shape[0])


# ---------------------------------------------------------------- compositing one frame
def frame_at(evs, segs, te, ts, frames):
    k = next(i for i, e in enumerate(evs) if e["e0"] <= te < e["e1"] or i == len(evs) - 1)
    ev = evs[k]
    img = draw(ev, te, ts, frames, segs)
    w_self, other = 1.0, None
    if k > 0 and te - ev["e0"] < XF / 2:
        other, w_self = evs[k - 1], ease(0.5 + (te - ev["e0"]) / XF)
    elif k + 1 < len(evs) and ev["e1"] - te < XF / 2:
        other, w_self = evs[k + 1], ease(0.5 + (ev["e1"] - te) / XF)
    if other is not None and w_self < 1:
        img = img * w_self + draw(other, te, ts, frames, segs) * (1 - w_self)
    img = scrims(img, ev["kind"])
    if ev["kind"] != "end":
        wm = 0.9 if other is None or other["kind"] != "end" else 0.9 * w_self
        watermark(img, wm)
    # bubbles: crossfade when the bubble person changes between neighbouring events
    bubs = {}
    mine, theirs = bub_key(ev["bubble"]), bub_key(other["bubble"]) if other is not None else None
    if mine:
        bubs[mine] = w_self if theirs != mine else 1.0
    if theirs and theirs != mine:
        bubs[theirs] = bubs.get(theirs, 0) + (1 - w_self)
    for key, op in bubs.items():
        overlay_bubble(img, key, frames, op)
    return np.clip(img, 0, 255).astype(np.uint8)


def needed(evs, e0, e1):
    ps = set()
    for e in evs:
        if e["e1"] > e0 - XF and e["e0"] < e1 + XF:
            if e["kind"] == "spk":
                ps.add(e["arg"])
            if e["bubble"]:
                ps.add(bub_key(e["bubble"])[0])
    return ps


def render_job(job):
    kind, a, b, e0, path = job
    segs, speech, evs = timeline()
    w = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "fast", "-crf", "14", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    if kind == "speech":
        n = round((b - a) * FPS)
        ps = sorted(needed(evs, e0, e0 + b - a))
        readers = {p: open_person(p, a, n) for p in ps}
        for i in range(n):
            frames = {p: next(r) for p, r in readers.items()}
            w.stdin.write(frame_at(evs, segs, e0 + i / FPS, a + i / FPS, frames).tobytes())
    else:  # end card: logo animation, then hold
        anim = list(R.reader(ANIM, 0, round(2.8 * FPS), OW, OH))
        n = round(END_DUR * FPS)
        for i in range(n):
            frames = {"anim": anim[min(i, len(anim) - 1)]}
            w.stdin.write(frame_at(evs, segs, e0 + i / FPS, None, frames).tobytes())
    w.stdin.close(); w.wait()
    return path


# ---------------------------------------------------------------- captions + text (ASS)
def load_words():
    words = {}
    for p, fn in (("m", "milad"), ("h", "hooman")):
        ws = []
        for s in json.load(open(f"transcripts/{fn}.json"))["segments"]:
            ws += [w for w in s.get("words", []) if "موسیقی" not in w["word"]]
        words[p] = ws
    return words


def write_ass(segs, speech, evs, path):
    def ts(x):
        h, x = divmod(max(x, 0), 3600); m, s = divmod(x, 60)
        return f"{int(h)}:{int(m):02d}:{s:05.2f}"
    ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {OW}", f"PlayResY: {OH}", "WrapStyle: 0", "",
           "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           "Style: Cap,Vazirmatn,70,&H00FFFFFF,&H00FFFFFF,&H001B1815,&H90000000,1,0,0,0,100,100,0,0,1,5,1.5,5,60,60,0,1",
           "Style: Hook,Vazirmatn,96,&H00FFFFFF,&H00FFFFFF,&H003B2316,&H00000000,1,0,0,0,100,100,0,0,3,20,0,5,40,40,0,1",
           "Style: Name,Vazirmatn,40,&H00FFFFFF,&H00FFFFFF,&H003B2316,&H00000000,1,0,0,0,100,100,0,0,3,12,0,5,0,0,0,1",
           "Style: Cta,Vazirmatn,66,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1",
           "Style: Link,Vazirmatn,46,&H00BEB2AA,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,1,0,1,0,0,5,0,0,0,1",
           "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    ev = lambda s, e, st, txt: ass.append(f"Dialogue: 0,{ts(s)},{ts(e)},{st},,0,0,0,,{R.rtl(txt)}")

    hook_end = evs[0]["e1"]
    ev(0.0, hook_end, "Hook", r"{\pos(540,360)\fad(0,250)}" + HOOK[0])
    ev(0.0, hook_end, "Hook", r"{\pos(540,505)\fad(0,250)\1c&H004BB8F2&}" + HOOK[1])

    shown = set()
    for e in evs:
        if e["kind"] == "spk" and e["arg"] not in shown:
            shown.add(e["arg"])
            ev(e["e0"] + 0.25, min(e["e1"] - 0.2, e["e0"] + 3.2), "Name", r"{\pos(540,1275)\fad(250,250)}" + NAMES[e["arg"]])

    end = evs[-1]
    ev(end["e0"] + 1.5, end["e1"], "Cta", r"{\pos(540,1380)\fad(400,0)}" + CTA[0])
    ev(end["e0"] + 1.8, end["e1"], "Link", r"{\pos(540,1475)\fad(400,0)}" + CTA[1])

    # word-timed caption chunks (max 4 words), suppressed where a card already shows the words
    silent = [(e["e0"], e["e1"]) for e in evs if e["kind"] in ("book", "quote", "lesson", "end")]
    words = load_words()
    for a, b, who, text in CLIP["cues"]:
        W = [w for w in words[who] if a - 0.05 <= w["start"] < b]
        corr = [x for piece in text.split("|") for x in [piece.split()]]
        flat = [w for piece in corr for w in piece]
        if not W or not flat:
            continue
        chunks, idx = [], 0
        for piece in corr:
            for i in range(0, len(piece), 4):
                chunk = piece[i : i + 4]
                if len(chunk) == 1 and chunks and i > 0:
                    chunks[-1] = (chunks[-1][0], chunks[-1][1] + chunk)
                else:
                    chunks.append((idx + i, chunk))
            idx += len(piece)
        for n, (i0, chunk) in enumerate(chunks):
            j0 = min(int(i0 * len(W) / len(flat)), len(W) - 1)
            s0 = W[j0]["start"]
            if n + 1 < len(chunks):
                j1 = min(int(chunks[n + 1][0] * len(W) / len(flat)), len(W) - 1)
                s1 = W[j1]["start"]
            else:
                s1 = min(b, W[-1]["end"] + 0.3)
            e0, e1 = to_edit(segs, s0), to_edit(segs, s1)
            if e1 - e0 < 0.2 or any(x0 - 0.05 <= e0 < x1 for x0, x1 in silent):
                continue
            ev(e0, e1, "Cap", r"{\pos(540,1385)\fad(80,60)}" + " ".join(chunk))
    open(path, "w").write("\n".join(ass) + "\n")


# ---------------------------------------------------------------- audio
def build_audio(segs, speech, evs, out):
    voice = ("highpass=f=85,lowpass=f=14000,afftdn=nf=-32:tn=1,equalizer=f=200:t=q:w=1:g=-2,"
             "equalizer=f=3200:t=q:w=1.2:g=2.5,deesser=i=0.35,acompressor=threshold=-24dB:ratio=3:attack=8:release=160:makeup=3,"
             "loudnorm=I=-19:TP=-3:LRA=8")
    lo, hi = segs[0][0] - 1, segs[-1][1] + 1
    subprocess.run([FF, "-v", "error", "-y", "-ss", str(lo), "-t", str(hi - lo), "-i", R.SRC["m"], "-ss", str(lo), "-t", str(hi - lo), "-i", R.SRC["h"],
                    "-filter_complex", f"[0:a]{voice}[a];[1:a]{voice}[b];[a][b]amix=inputs=2:normalize=0,aresample=48000[o]",
                    "-map", "[o]", "-c:a", "pcm_s16le", "work/s2_mix.wav"], check=True)
    total = speech + END_DUR
    fc, parts = [], []
    for i, (a, b, _) in enumerate(segs):
        fc.append(f"[0:a]atrim={a-lo:.4f}:{b-lo:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={b-a-0.01:.4f}:d=0.01[s{i}]")
        parts.append(f"[s{i}]")
    fc.append("".join(parts) + f"concat=n={len(parts)}:v=0:a=1,apad=whole_dur={total:.3f},aformat=sample_rates=48000:channel_layouts=stereo[v]")
    T_build = next(e["e0"] for e in evs if e["s0"] == 1799.74)
    T_theme = next(e["e0"] for e in evs if e["s0"] == 1821.96)
    T_end = speech
    st = "aformat=sample_rates=48000:channel_layouts=stereo"
    g0 = T_theme - 20.0  # the build cue decays at ~20s: land that decay exactly where the theme enters
    b_len = g0 + 1.5
    fc.append(f"[1:a]{st},atrim=8:{8 + b_len:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.5,afade=t=out:st={b_len-1.5:.3f}:d=1.5,volume=-5.5dB[bed]")
    g_len = 21.0
    fc.append(f"[2:a]{st},atrim=0:{g_len:.3f},afade=t=in:d=1.5,volume=-5.5dB,"
              f"adelay={int(g0*1000)}|{int(g0*1000)}[bld]")
    t0 = T_theme - 0.6
    t_len = T_end + 3.8 - t0
    fc.append(f"[3:a]{st},atrim=0:{t_len:.3f},afade=t=in:d=0.8,afade=t=out:st={t_len-3.3:.3f}:d=3.3,volume=-13dB,"
              f"adelay={int(t0*1000)}|{int(t0*1000)}[thm]")
    fc.append(f"[4:a]{st},volume=8dB,adelay={int((T_end+0.05)*1000)}|{int((T_end+0.05)*1000)}[sig]")
    fc.append("[bed][bld][thm]amix=inputs=3:normalize=0[mus]")
    fc.append("[v]asplit[v1][v2]")
    fc.append("[mus][v2]sidechaincompress=threshold=0.03:ratio=4:attack=30:release=380[duck]")
    fc.append(f"[v1][duck][sig]amix=inputs=3:normalize=0,atrim=0:{total:.3f}[o]")
    open("work/s2_afilter.txt", "w").write(";\n".join(fc))
    subprocess.run([FF, "-v", "error", "-y", "-i", "work/s2_mix.wav", "-i", MUSIC.format("conversation-bed"),
                    "-i", MUSIC.format("build-and-reveal"), "-i", MUSIC.format("main-theme"), "-i", SIGNATURE,
                    "-/filter_complex", "work/s2_afilter.txt", "-map", "[o]", "-c:a", "pcm_s16le", "work/s2_pre.wav"], check=True)
    m = subprocess.run([FF, "-hide_banner", "-i", "work/s2_pre.wav", "-af", "loudnorm=I=-14:TP=-2:LRA=9:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
    ln = (f"loudnorm=I=-14:TP=-2:LRA=9:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}"
          f":measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run([FF, "-v", "error", "-y", "-i", "work/s2_pre.wav", "-af", ln + ",aresample=48000", "-c:a", "pcm_s16le", out], check=True)
    return dict(build=T_build, theme=T_theme, end=T_end)


# ---------------------------------------------------------------- main
def finalize():
    """Redo text + audio + final encode, reusing the rendered picture."""
    segs, speech, evs = timeline()
    d = "work/short2_parking"
    total = speech + END_DUR
    write_ass(segs, speech, evs, f"{d}/text.ass")
    marks = build_audio(segs, speech, evs, f"{d}/audio.wav")
    print("music marks", {k: round(v, 2) for k, v in marks.items()})
    mux(d, total)


def mux(d, total):
    subprocess.run([FF, "-v", "error", "-y", "-i", f"{d}/video.mp4", "-i", f"{d}/audio.wav",
                    "-vf", f"ass={d}/text.ass:fontsdir={FONTDIR},noise=alls=3:allf=t,fade=in:d=0.2",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-profile:v", "high", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-t", f"{total:.3f}", OUT], check=True)
    print("wrote", OUT, f"{total:.1f}s")


def main():
    segs, speech, evs = timeline()
    d = "work/short2_parking"
    os.makedirs(d, exist_ok=True)
    jobs = [("speech", a, b, e0, f"{d}/{i:03d}.mp4") for i, (a, b, e0) in enumerate(segs)]
    jobs.append(("end", 0, 0, speech, f"{d}/end.mp4"))
    total = speech + END_DUR
    print(f"{len(segs)} speech segments, {speech:.1f}s + {END_DUR}s end card", flush=True)
    for e in evs:
        print(f"  {e['e0']:6.2f}-{e['e1']:6.2f} {e['kind']:6s} {e['arg'][0] if e['kind']=='img' else e['arg'] or ''} bubble={e['bubble']}")
    with Pool(6) as pool:
        files = pool.map(render_job, jobs)
    with open(f"{d}/concat.txt", "w") as f:
        f.writelines(f"file '{os.path.basename(x)}'\n" for x in files)
    subprocess.run([FF, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{d}/concat.txt", "-c", "copy", f"{d}/video.mp4"], check=True)
    write_ass(segs, speech, evs, f"{d}/text.ass")
    marks = build_audio(segs, speech, evs, f"{d}/audio.wav")
    print("music marks", {k: round(v, 2) for k, v in marks.items()})
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    mux(d, total)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "finalize":
        finalize()
        sys.exit()
    if len(sys.argv) > 2 and sys.argv[1] == "still":
        T = float(sys.argv[2])
        segs, speech, evs = timeline()
        if T >= speech:
            anim = list(R.reader(ANIM, 0, round(2.8 * FPS), OW, OH))
            fr_ = frame_at(evs, segs, T, None, {"anim": anim[min(int((T - speech) * FPS), len(anim) - 1)]})
        else:
            a, b, e0 = next(s for s in segs if s[2] <= T < s[2] + s[1] - s[0])
            ts_ = a + (T - e0)
            frames = {p: next(open_person(p, ts_, 1)) for p in needed(evs, T, T)}
            fr_ = frame_at(evs, segs, T, ts_, frames)
        cv2.imwrite("work/s2_still.jpg", cv2.cvtColor(fr_, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 92])
        print("ok", T)
        sys.exit()
    main()
