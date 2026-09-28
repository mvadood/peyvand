import json, os, subprocess, sys
import numpy as np
from captions_test import CUES, MANUAL_CUTS, BOOK_CARD, AUTHORS_CARD

FF = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
D = os.path.expanduser("~/Downloads/2024-07-08--t10-46-31am")
SRC = {"m": f"{D}--6686af0927a13c251c09b980--mvadood.mov", "h": f"{D}--guest329206--hooman.mov"}
RANGE = (1.5, 201.8)
FPS = 30
HOP = 0.1
INTRO = 3.5
OUT = "test_cut.mp4"
os.makedirs("segs", exist_ok=True)

def fr(t):  # snap to frame grid
    return round(t * FPS) / FPS

# ---------- 1. what to keep ----------
state = np.load("state.npy")
t = np.arange(len(state)) * HOP
keep = (t >= RANGE[0]) & (t < RANGE[1])
for a, b in MANUAL_CUTS:
    keep &= ~((t >= a) & (t < b))
# shorten pauses: silent runs >= 0.7s keep 0.15s head + 0.2s tail
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

intervals = []
i = 0
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

# ---------- 2. shot per kept frame ----------
frames = [k for k in range(len(keep)) if keep[k]]
raw = []
last = "M"
for k in frames:
    s = state[k]
    last = {"M": "M", "H": "H", "B": "S"}.get(s, last)
    raw.append(last)

# runs in edited time, absorb runs shorter than 1.6s into the previous shot
runs = []
for k, s in zip(frames, raw):
    if runs and runs[-1][0] == s:
        runs[-1][2] += 1
    else:
        runs.append([s, k, 1])
merged = []
for s, k, n in runs:
    if merged and (n * HOP < 1.6 or merged[-1][0] == s):
        merged[-1][2] += n
    else:
        merged.append([s, k, n])

# expand runs into frame-level shot labels with framing variety on long runs
cut_points = set()
for a, b in intervals:
    cut_points.add(round(a / HOP))
label = {}
pos = 0
for s, k0, n in merged:
    run_frames = frames[pos : pos + n]
    pos += n
    if s == "S" or n * HOP < 9:
        v = {"M": "Mw", "H": "Hw", "S": "S"}[s]
        for k in run_frames:
            label[k] = v
        continue
    cycle = [s + "w", s + "c", "S", s + "c"]
    ci, since = 0, 0
    for idx, k in enumerate(run_frames):
        since += 1
        remaining = len(run_frames) - idx
        at_jump = k in cut_points
        if remaining > 30 and ((since >= 50 and at_jump) or since >= 80):
            ci, since = ci + 1, 0
        label[k] = cycle[ci % len(cycle)]

# ---------- 3. segments = kept intervals split on label change ----------
segs = []
for a, b in intervals:
    ks = [k for k in range(round(a / HOP), round(b / HOP)) if keep[k]]
    cur, start = label[ks[0]], ks[0]
    for k in ks[1:] + [None]:
        if k is None or label[k] != cur:
            end = (k if k is not None else ks[-1] + 1)
            segs.append((fr(start * HOP), fr(end * HOP), cur))
            if k is not None:
                cur, start = label[k], k
# merge adjacent identical shots that are contiguous in source
out = []
for s in segs:
    if out and out[-1][2] == s[2] and abs(out[-1][1] - s[0]) < 1e-6:
        out[-1] = (out[-1][0], s[1], s[2])
    else:
        out.append(s)
segs = out
json.dump(segs, open("edl.json", "w"))
total = sum(b - a for a, b, _ in segs)
print(f"{len(segs)} segments, {total:.1f}s edited from {RANGE[1]-RANGE[0]:.1f}s source")

def src_to_edit(ts, side):
    acc = INTRO
    for a, b, _ in segs:
        if ts < a:
            return acc if side == "start" else (acc if acc > INTRO else None)
        if ts <= b:
            return acc + (ts - a)
        acc += b - a
    return acc

# ---------- 4. video framing ----------
GRADE = {"m": "eq=contrast=1.04:saturation=1.08", "h": "eq=contrast=1.06:saturation=1.1:gamma=1.03,unsharp=5:5:0.6"}
DIM = {"m": (2560, 1440), "h": (1920, 1080)}
FACE = {"m": (0.5, 0.42), "h": (0.515, 0.60)}

def crop(p, z, aspect, cy=None, ow=1920, oh=1080):
    W, H = DIM[p]
    cx, fcy = FACE[p]
    cy = fcy if cy is None else cy
    h = H / z
    w = h * aspect
    if w > W:
        w = W; h = w / aspect
    x = min(max(cx * W - w / 2, 0), W - w)
    y = min(max(cy * H - h / 2, 0), H - h)
    return f"crop={int(w)//2*2}:{int(h)//2*2}:{int(x)}:{int(y)},scale={ow}:{oh}:flags=lanczos,{GRADE[p]}"

FULL = {
    "Mw": ("m", crop("m", 1.0, 16 / 9, cy=0.5)),
    "Mc": ("m", crop("m", 1.45, 16 / 9)),
    "Hw": ("h", crop("h", 1.15, 16 / 9, cy=0.56)),
    "Hc": ("h", crop("h", 1.45, 16 / 9)),
}
PW, PH = 936, 1016
SPLIT = (f"[0:v]{crop('m', 1.1, PW/PH, ow=PW, oh=PH)}[l];"
         f"[1:v]{crop('h', 1.15, PW/PH, ow=PW, oh=PH)}[r];"
         f"color=c=0x15171a:s=1920x1080:r={FPS}[bg];"
         f"[bg][l]overlay=16:32:shortest=1[t];[t][r]overlay=968:32:shortest=1,format=yuv420p[v]")

ENC = ["-c:v", "libx264", "-preset", "fast", "-crf", "14", "-pix_fmt", "yuv420p", "-r", str(FPS), "-an"]

def render(i, a, b, shot):
    fn = f"segs/{i:04d}.mp4"
    dur = f"{b - a:.4f}"
    if shot == "S":
        cmd = [FF, "-v", "error", "-y", "-ss", f"{a:.4f}", "-t", dur, "-i", SRC["m"], "-ss", f"{a:.4f}", "-t", dur, "-i", SRC["h"],
               "-filter_complex", SPLIT, "-map", "[v]", "-frames:v", str(round((b - a) * FPS))] + ENC + [fn]
    else:
        p, vf = FULL[shot]
        cmd = [FF, "-v", "error", "-y", "-ss", f"{a:.4f}", "-t", dur, "-i", SRC[p], "-vf", vf,
               "-frames:v", str(round((b - a) * FPS))] + ENC + [fn]
    subprocess.run(cmd, check=True)
    return fn

from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(6) as ex:
    files = list(ex.map(lambda x: render(x[0], *x[1]), enumerate(segs)))

# intro card background: blurred, darkened split frame
subprocess.run([FF, "-v", "error", "-y", "-ss", "20", "-i", SRC["m"], "-ss", "20", "-i", SRC["h"], "-filter_complex",
                SPLIT.replace("format=yuv420p[v]", "boxblur=30:3,eq=brightness=-0.25,format=yuv420p[v]"),
                "-map", "[v]", "-frames:v", "1", "intro_bg.png"], check=True)
subprocess.run([FF, "-v", "error", "-y", "-loop", "1", "-i", "intro_bg.png", "-t", str(INTRO), "-vf",
                f"fade=in:0:15,fade=out:st={INTRO-0.4}:d=0.4"] + ENC + ["segs/intro.mp4"], check=True)

with open("concat.txt", "w") as f:
    for fn in ["segs/intro.mp4"] + files:
        f.write(f"file '{fn}'\n")
subprocess.run([FF, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "concat.txt", "-c", "copy", "video_raw.mp4"], check=True)

# ---------- 5. audio: clean each voice, mix, cut to EDL, master ----------
voice = "highpass=f=80,afftdn=nf=-30,acompressor=threshold=-24dB:ratio=3:attack=8:release=160:makeup=3,loudnorm=I=-19:TP=-3:LRA=8"
subprocess.run([FF, "-v", "error", "-y", "-ss", "0", "-t", str(RANGE[1] + 1), "-i", SRC["m"], "-ss", "0", "-t", str(RANGE[1] + 1), "-i", SRC["h"],
                "-filter_complex", f"[0:a]{voice}[a];[1:a]{voice}[b];[a][b]amix=inputs=2:normalize=0,aresample=48000[o]",
                "-map", "[o]", "-c:a", "pcm_s16le", "mix.wav"], check=True)
parts = []
fc = []
for i, (a, b, _) in enumerate(segs):
    fc.append(f"[0:a]atrim={a:.4f}:{b:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={b-a-0.012:.4f}:d=0.012[s{i}]")
    parts.append(f"[s{i}]")
fc.append(f"anullsrc=r=48000:cl=mono,atrim=0:{INTRO}[pre]")
fc.append("[pre]" + "".join(parts) + f"concat=n={len(parts)+1}:v=0:a=1[cut]")
open("afilter.txt", "w").write(";\n".join(fc))
subprocess.run([FF, "-v", "error", "-y", "-i", "mix.wav", "-/filter_complex", "afilter.txt", "-map", "[cut]", "-c:a", "pcm_s16le", "cut.wav"], check=True)
m = subprocess.run([FF, "-hide_banner", "-i", "cut.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"],
                   capture_output=True, text=True).stderr
js = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
ln = (f"loudnorm=I=-14:TP=-1.5:LRA=9:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}"
      f":measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
subprocess.run([FF, "-v", "error", "-y", "-i", "cut.wav", "-af", ln + ",aresample=48000", "-ac", "2", "-c:a", "pcm_s16le", "master.wav"], check=True)

# ---------- 6. subtitles / graphics (ASS) ----------
def ts(x):
    h, x = divmod(x, 3600); mnt, s = divmod(x, 60)
    return f"{int(h)}:{int(mnt):02d}:{s:05.2f}"

ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 0", "",
       "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Cap,Geeza Pro,58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,1,0,0,0,100,100,0,0,1,3.5,1.5,2,120,120,70,1",
       "Style: Name,Geeza Pro,46,&H00FFFFFF,&H00FFFFFF,&H00202020,&H00000000,1,0,0,0,100,100,0,0,3,14,0,1,80,80,190,1",
       "Style: Tag,Geeza Pro,34,&H00FFFFFF,&H00FFFFFF,&H00202020,&H00000000,1,0,0,0,100,100,0,0,3,10,0,7,0,0,0,1",
       "Style: Card,Helvetica Neue,44,&H00FFFFFF,&H00FFFFFF,&H00202020,&H00000000,1,0,0,0,100,100,0,0,3,18,0,7,70,70,60,1",
       "Style: Title,Helvetica Neue,110,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1",
       "Style: Sub,Geeza Pro,52,&H0033B5FF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1",
       "Style: Small,Helvetica Neue,38,&H00C8C8C8,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
ev = lambda s, e, st, txt, layer=0: ass.append(f"Dialogue: {layer},{ts(s)},{ts(e)},{st},,0,0,0,,{txt}")
fade = r"{\fad(250,250)}"

# intro title
ev(0.2, INTRO - 0.2, "Title", r"{\fad(300,300)\pos(960,440)}Are Your Lights On?")
ev(0.5, INTRO - 0.2, "Sub", r"{\fad(300,300)\pos(960,580)}گفتگو درباره‌ی کتاب «آیا چراغ‌هات روشنه؟»")
ev(0.8, INTRO - 0.2, "Small", r"{\fad(300,300)\pos(960,670)}Donald C. Gause  ·  Gerald M. Weinberg")

# captions (hide while split-screen name tags would clash? keep; they sit in the bottom gutter)
for a, b, who, text in CUES:
    pieces = text.split("|")
    span = b - a
    tot = sum(len(p) for p in pieces)
    t0 = a
    for p in pieces:
        t1 = t0 + span * len(p) / tot
        s, e = src_to_edit(t0, "start"), src_to_edit(t1, "end")
        if e is not None and e - s > 0.25:
            ev(s, e, "Cap", p)
        t0 = t1

# name lower-thirds on first full-frame appearance of each person, tags on split screens
shown = set()
acc = INTRO
for a, b, shot in segs:
    if shot in ("Mw", "Mc", "Hw", "Hc") and shot[0] not in shown and b - a > 2:
        shown.add(shot[0])
        ev(acc + 0.3, acc + min(4.5, b - a - 0.2), "Name", fade + ("میلاد" if shot[0] == "M" else "هومن"))
    if shot == "S":
        ev(acc, acc + (b - a), "Tag", r"{\pos(40,56)}میلاد", 1)
        ev(acc, acc + (b - a), "Tag", r"{\pos(992,56)}هومن", 1)
    acc += b - a

# book + author cards
s, e = src_to_edit(BOOK_CARD[0], "start"), src_to_edit(BOOK_CARD[1], "end")
ev(s, e, "Card", fade + r"Are Your Lights On?\N{\fs30\b0}How to Figure Out What the Problem Really Is")
s, e = src_to_edit(AUTHORS_CARD[0], "start"), src_to_edit(AUTHORS_CARD[1], "end")
ev(s, e, "Card", fade + r"{\fs36}Gerald M. Weinberg  ·  Donald C. Gause")
open("graphics.ass", "w").write("\n".join(ass) + "\n")

# ---------- 7. final ----------
total_len = INTRO + total
subprocess.run([FF, "-v", "error", "-y", "-i", "video_raw.mp4", "-i", "master.wav",
                "-vf", f"ass=graphics.ass,fade=out:st={total_len-0.6:.3f}:d=0.6",
                "-af", f"afade=t=out:st={total_len-0.6:.3f}:d=0.6",
                "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-pix_fmt", "yuv420p",
                "-g", "15", "-bf", "2", "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-movflags", "+faststart",
                "-shortest", OUT], check=True)
print("wrote", OUT, f"{total_len:.1f}s")
