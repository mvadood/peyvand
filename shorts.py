"""Vertical 1080x1920 shorts/reels from the conversation.

python shorts.py NAME [NAME ...]      render clips (tunnel, parking, salary, definition)
python shorts.py still NAME T         one frame at clip time T -> work/short_still.jpg
"""
import json, os, subprocess, sys
from multiprocessing import Pool

import cv2
import numpy as np

import render_poc as R
from shorts_cues import ALPHA_FILES, CLIPS

FF, FPS, HOP = R.FF, R.FPS, R.HOP
OW, OH = 1080, 1920
HALF = 960


def alpha_for(p, a):
    for s, e, path in ALPHA_FILES[p]:
        if s <= a < e:
            return path, a - s, e
    raise ValueError(f"no matte for {p} at {a}")


def open_person(p, a, n):
    W, H = R.DIM[p]
    path, at, _ = alpha_for(p, a)
    return zip(R.reader(R.SRC[p], a, n, W, H), R.reader(path, at, n, W, H, gray=True))


# ---------------------------------------------------------------- edit list
def build(clip):
    c = CLIPS[clip]
    state = np.load("work/state.npy")
    t = np.arange(len(state)) * HOP
    keep = np.zeros(len(state), bool)
    for a, b in c["ranges"]:
        keep |= (t >= a) & (t < b)
    i = 0
    while i < len(state):  # tighter pause trimming for shorts: keep 0.1s + 0.15s
        if state[i] == "-":
            j = i
            while j < len(state) and state[j] == "-":
                j += 1
            if (j - i) * HOP >= 0.5:
                keep[i + 1 : j - 1] = False
            i = j
        else:
            i += 1

    def win(ts, spans):
        return next((x for x in spans if x[0] <= ts < x[1]), None)

    # frame-level layout labels
    labels, last, last_v = {}, None, None
    for k in np.nonzero(keep)[0]:
        ts = k * HOP
        g = win(ts, c["graphics"])
        if win(ts, c["tunnel"]):
            lab = "I"
        elif g:
            spk = {"M": "m", "H": "h"}.get(state[k], last[1] if last and last[0] in "VG" else "h")
            lab = f"G{spk}:{g[2]}"
        else:
            s = state[k]
            if s in "MH":
                lab = "V" + s.lower()
            elif s == "B":
                lab = "S"
            else:
                lab = last_v or "Vh"
        labels[k] = lab
        last = lab
        if lab[0] in "VS":
            last_v = lab
    # absorb short flickers (<1.2s) into the previous label, except graphics/tunnel windows
    ks = sorted(labels)
    runs = []
    for k in ks:
        if runs and runs[-1][0] == labels[k] and k == runs[-1][2] + 1:
            runs[-1][2] = k
        else:
            runs.append([labels[k], k, k])
    for r_i in range(1, len(runs)):
        lab, k0, k1 = runs[r_i]
        if (k1 - k0 + 1) * HOP < 1.2 and lab[0] in "VS" and runs[r_i - 1][0][0] in "VS":
            runs[r_i][0] = runs[r_i - 1][0]
            for k in range(k0, k1 + 1):
                labels[k] = runs[r_i][0]
    # segments: contiguous kept frames with same label, split at matte-file boundaries
    segs, cur = [], None
    for k in ks:
        ts = R.fr(k * HOP)
        lab = labels[k]
        boundary = any(abs(ts - s) < 1e-6 for p in "hm" for s, _, _ in ALPHA_FILES[p][1:])
        if cur and cur[2] == lab and abs(cur[1] - ts) < 1e-6 and not boundary:
            cur[1] = R.fr(ts + HOP)
        else:
            if cur:
                segs.append(cur)
            cur = [ts, R.fr(ts + HOP), lab]
    segs.append(cur)
    segs = [s for s in segs if s[1] - s[0] >= 2 / FPS]
    # break long talking shots into ~7s pieces so the framing alternates (punch-in cuts)
    split = []
    for a, b, lab in segs:
        if lab[0] == "V" and b - a > 9:
            n = int((b - a) // 7)
            step = (b - a) / n
            for i in range(n):
                split.append([R.fr(a + i * step), R.fr(a + (i + 1) * step) if i < n - 1 else b, lab])
        else:
            split.append([a, b, lab])
    segs = split
    # timeline + zoom variety: alternate punch-in on consecutive same-person shots (hides jump cuts)
    acc, prev, alt, spans = 0.0, None, 0, {}
    for s in segs:
        if s[2] == prev:
            alt ^= 1
        else:
            alt = 0
        s += [acc, alt]
        spans.setdefault(s[2] + str(round(s[0])), None)
        acc += s[1] - s[0]
        prev = s[2]
    # group spans for graphics/tunnel animation (edited-time extent of each window)
    gspan = {}
    for s in segs:
        key = s[2] if s[2][0] in "GI" else None
        if key:
            w = next((x for x in c["graphics"] + [(a, b, "I") for a, b in c["tunnel"]] if x[0] <= s[0] < x[1]), None)
            if w is None:
                raise ValueError(f"no window for {s}")
            gk = (key, w[0])
            e0, e1 = gspan.get(gk, (s[3], s[3]))
            gspan[gk] = (min(e0, s[3]), s[3] + s[1] - s[0])
            s.append(gk)
        else:
            s.append(None)
    return segs, gspan, acc


# ---------------------------------------------------------------- frames
VFRAME = {"m": (1.0, 0.5, 0.45), "h": (1.12, 0.515, 0.6)}  # full-height vertical framing
BG = None


def vertical(p, f, a, alt, ow=OW, oh=OH, lift=0.0):
    z, cx, cy = VFRAME[p]
    z *= 1.14 if alt else 1.0
    return R.compose_person(p, f, a, z, cx, cy + lift, ow, oh)


def backdrop(h=HALF):
    global BG
    if BG is None:
        bg = R.asset("bg_hooman")
        BG = cv2.resize(bg[:, 420:1500], (OW, OH))
    return BG[:h].copy()


def tunnel_v(t_rel, dur, t_src):
    scene, lights = R.asset("tunnel"), R.asset("tunnel_lights")
    img = scene.copy()
    k = R.ease((t_src - R.HEADLIGHTS_ON) / 0.6)
    if k > 0:
        al = lights[..., 3:4].astype(np.float32) / 255 * k
        img[..., :3] = (img[..., :3] * (1 - al) + lights[..., :3] * al).astype(np.uint8)
    img = img[..., :3]
    z = 1.0 + 0.12 * R.ease(t_rel / max(dur, 1e-3))
    sh = int(1300 * z)
    sw = int(img.shape[1] * sh / img.shape[0])
    big = cv2.resize(img, (sw, sh), interpolation=cv2.INTER_CUBIC)
    out = np.empty((OH, OW, 3), np.uint8)
    out[:] = img[0, 0]
    top = int(OH * 0.44 - sh * 0.42)
    x0 = (sw - OW) // 2
    y0, y1 = max(top, 0), min(top + sh, OH)
    out[y0:y1] = big[y0 - top : y1 - top, x0 : x0 + OW]
    if y1 < OH:  # extend the road downward
        out[y1:] = cv2.GaussianBlur(np.repeat(out[y1 - 1 : y1], OH - y1, 0), (0, 0), 8)
    if y0 > 0:
        out[:y0] = np.linspace(np.array([8, 12, 26]), out[y0].mean(0), y0)[:, None, :].astype(np.uint8)
    return out


def graphic_panel(name, t_rel, span, t_src):
    panel = backdrop()
    k = min(R.ease(t_rel / 0.4), R.ease((span - t_rel) / 0.3))
    if name == "sign3":
        n = sum(1 for x in R.SIGN3_LINES if t_src >= x - 0.05) or 1
        img, sc = R.asset(f"sign3_{n}"), 1.0
    else:
        img = R.asset(name)
        sc = min(1.0, 1000 / img.shape[1])
    R.overlay(panel, img, OW / 2, HALF * 0.55 + (1 - k) * 40, sc, k)
    return panel


def render_segment(job):
    (a, b, lab, e0, alt, gk), gspan, clip, out_path = job
    n = round((b - a) * FPS)
    if os.environ.get("REUSE") and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        return out_path
    w = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "fast", "-crf", "14", "-pix_fmt", "yuv420p", out_path], stdin=subprocess.PIPE)
    if lab == "I":
        src = ((None,) for _ in range(n))
    elif lab == "S":
        src = zip(open_person("m", a, n), open_person("h", a, n))
    elif lab[0] == "G":
        src = ((x,) for x in open_person(lab[1], a, n))
    else:
        src = ((x,) for x in open_person(lab[1], a, n))
    for i, fr_ in enumerate(src):
        te, ts = e0 + i / FPS, a + i / FPS
        if lab == "I":
            g0, g1 = gspan[gk]
            out = tunnel_v(te - g0, g1 - g0, ts)
            kf = min(1.0, (te - g0) * FPS / 5 + 0.2, (g1 - te) * FPS / 5)
            out = (out * max(kf, 0)).astype(np.uint8)
        elif lab == "S":
            (fm, am), (fh, ah) = fr_
            out = np.empty((OH, OW, 3), np.uint8)
            out[:HALF] = R.compose_person("m", fm, am, 1.25, 0.5, 0.42, OW, HALF)
            out[HALF:] = R.compose_person("h", fh, ah, 1.45, 0.515, 0.6, OW, HALF)
            out[HALF - 3 : HALF + 3] = (255, 200, 90)
        elif lab[0] == "G":
            (f, al), = fr_
            g0, g1 = gspan[gk]
            out = np.empty((OH, OW, 3), np.uint8)
            out[:HALF] = graphic_panel(lab.split(":")[1], te - g0, g1 - g0, ts)
            p = lab[1]
            out[HALF:] = R.compose_person(p, f, al, 1.3 if p == "m" else 1.5, 0.5 if p == "m" else 0.515, 0.42 if p == "m" else 0.6, OW, HALF)
            out[HALF - 3 : HALF + 3] = (255, 200, 90)
        else:
            (f, al), = fr_
            out = vertical(lab[1], f, al, alt)
        w.stdin.write(np.ascontiguousarray(out).tobytes())
    w.stdin.close(); w.wait()
    return out_path


# ---------------------------------------------------------------- text + audio
def to_edit(segs, ts):
    for a, b, lab, e0, *_ in segs:
        if ts < a:
            return e0
        if ts <= b:
            return e0 + ts - a
    return segs[-1][3] + segs[-1][1] - segs[-1][0]


def write_ass(clip, segs, total, path):
    c = CLIPS[clip]
    def ts(x):
        h, x = divmod(max(x, 0), 3600); m, s = divmod(x, 60)
        return f"{int(h)}:{int(m):02d}:{s:05.2f}"
    ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {OW}", f"PlayResY: {OH}", "WrapStyle: 0", "",
           "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           "Style: Cap,SF Arabic,74,&H00FFFFFF,&H00FFFFFF,&H00000000,&H99000000,1,0,0,0,100,100,0,0,1,6,2,5,70,70,0,1",
           "Style: Hook,SF Arabic,70,&H00101010,&H00FFFFFF,&H005AC8FF,&H00000000,1,0,0,0,100,100,0,0,3,22,0,8,60,60,190,1",
           "Style: Tag,DIN Alternate,34,&H00DCDCDC,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,2,0,1,2,0,8,60,60,110,1",
           "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    ev = lambda s, e, st, txt: ass.append(f"Dialogue: 0,{ts(s)},{ts(e)},{st},,0,0,0,,{R.rtl(txt)}")
    ev(0.0, 4.2, "Hook", r"{\fad(150,300)}" + c["hook"])
    ev(4.2, total, "Tag", r"{\fad(300,0)}ARE YOUR LIGHTS ON?  |  GAUSE & WEINBERG")
    # chunked captions: max ~4 words per card, timed proportionally inside each cue
    for a, b, who, text in c["cues"]:
        if b < c["ranges"][0][0] or a > c["ranges"][-1][1]:
            continue
        pieces = text.split("|")
        tot, t0 = sum(len(p) for p in pieces), a
        for piece in pieces:
            t1 = t0 + (b - a) * len(piece) / tot
            words = piece.split()
            chunks = [" ".join(words[i : i + 4]) for i in range(0, len(words), 4)]
            if len(chunks) > 1 and len(chunks[-1].split()) == 1:
                tail = chunks.pop()
                chunks[-1] += " " + tail
            cl = sum(len(x) for x in chunks)
            u = t0
            for ch in chunks:
                v = u + (t1 - t0) * len(ch) / cl
                s, e = to_edit(segs, u), to_edit(segs, v)
                if e - s > 0.2 and any(ra <= u < rb for ra, rb in c["ranges"]):
                    lab = next((sg[2] for sg in segs if sg[0] <= u < sg[1]), "V")
                    y = 850 if lab[0] == "G" else 960 if lab == "S" else 1590
                    ev(s, e, "Cap", rf"{{\pos(540,{y})\fscx92\fscy92\t(0,90,\fscx100\fscy100)}}" + ch)
                u = v
            t0 = t1
    open(path, "w").write("\n".join(ass) + "\n")


def build_audio(segs, total, out):
    voice = ("highpass=f=85,lowpass=f=14000,afftdn=nf=-32:tn=1,equalizer=f=200:t=q:w=1:g=-2,"
             "equalizer=f=3200:t=q:w=1.2:g=2.5,deesser=i=0.35,acompressor=threshold=-24dB:ratio=3:attack=8:release=160:makeup=3,"
             "loudnorm=I=-19:TP=-3:LRA=8")
    lo = min(s[0] for s in segs) - 1
    hi = max(s[1] for s in segs) + 1
    subprocess.run([FF, "-v", "error", "-y", "-ss", str(lo), "-t", str(hi - lo), "-i", R.SRC["m"], "-ss", str(lo), "-t", str(hi - lo), "-i", R.SRC["h"],
                    "-filter_complex", f"[0:a]{voice}[a];[1:a]{voice}[b];[a][b]amix=inputs=2:normalize=0,aresample=48000[o]",
                    "-map", "[o]", "-c:a", "pcm_s16le", "work/s_mix.wav"], check=True)
    fc, parts = [], []
    for i, (a, b, *_rest) in enumerate(segs):
        fc.append(f"[0:a]atrim={a-lo:.4f}:{b-lo:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={b-a-0.01:.4f}:d=0.01[s{i}]")
        parts.append(f"[s{i}]")
    fc.append("".join(parts) + f"concat=n={len(parts)}:v=0:a=1[v]")
    fc.append(f"[1:a]aloop=loop=-1:size=2e9,atrim=0:{total:.3f},volume=0.16,afade=t=in:d=1,afade=t=out:st={total-1.5:.3f}:d=1.5[mus]")
    fc.append("[v]asplit[v1][v2];[mus][v2]sidechaincompress=threshold=0.03:ratio=5:attack=40:release=600[duck];[v1][duck]amix=inputs=2:normalize=0[o]")
    open("work/s_afilter.txt", "w").write(";\n".join(fc))
    subprocess.run([FF, "-v", "error", "-y", "-i", "work/s_mix.wav", "-i", "assets/music.wav", "-/filter_complex", "work/s_afilter.txt",
                    "-map", "[o]", "-ac", "2", "-c:a", "pcm_s16le", "work/s_pre.wav"], check=True)
    m = subprocess.run([FF, "-hide_banner", "-i", "work/s_pre.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=8:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=8:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}"
          f":measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run([FF, "-v", "error", "-y", "-i", "work/s_pre.wav", "-af", ln + ",aresample=48000", "-c:a", "pcm_s16le", out], check=True)


def render_clip(clip):
    segs, gspan, total = build(clip)
    d = f"work/short_{clip}"
    os.makedirs(d, exist_ok=True)
    print(f"[{clip}] {len(segs)} segments, {total:.1f}s", flush=True)
    jobs = [(tuple(s), gspan, clip, f"{d}/{i:04d}.mp4") for i, s in enumerate(segs)]
    with Pool(5) as pool:
        files = pool.map(render_segment, jobs)
    with open(f"{d}/concat.txt", "w") as f:
        f.writelines(f"file '{os.path.basename(x)}'\n" for x in files)
    subprocess.run([FF, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{d}/concat.txt", "-c", "copy", f"{d}/video.mp4"], check=True)
    write_ass(clip, segs, total, f"{d}/text.ass")
    build_audio(segs, total, f"{d}/audio.wav")
    os.makedirs("renders/shorts", exist_ok=True)
    out = f"renders/shorts/{clip}.mp4"
    subprocess.run([FF, "-v", "error", "-y", "-i", f"{d}/video.mp4", "-i", f"{d}/audio.wav",
                    "-vf", f"ass={d}/text.ass,noise=alls=3:allf=t,fade=in:d=0.25,fade=out:st={total-0.4:.3f}:d=0.4",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", out], check=True)
    print(f"[{clip}] wrote {out} ({total:.1f}s)", flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "still":
        clip, T = sys.argv[2], float(sys.argv[3])
        segs, gspan, total = build(clip)
        for s in segs:
            if s[3] <= T < s[3] + s[1] - s[0]:
                a = s[0] + T - s[3]
                one = (a, a + 1 / FPS, s[2], T, s[4], s[5])
                render_segment((one, gspan, clip, "work/short_still.mp4"))
                subprocess.run([FF, "-v", "error", "-y", "-i", "work/short_still.mp4", "-frames:v", "1", "work/short_still.jpg"], check=True)
                print(s[2], f"src {a:.2f}")
                break
        sys.exit()
    for clip in sys.argv[1:]:
        render_clip(clip)


def finalize(clip):
    """Redo only the text layer + mux, reusing the rendered video and audio."""
    segs, gspan, total = build(clip)
    d = f"work/short_{clip}"
    write_ass(clip, segs, total, f"{d}/text.ass")
    subprocess.run([FF, "-v", "error", "-y", "-i", f"{d}/video.mp4", "-i", f"{d}/audio.wav",
                    "-vf", f"ass={d}/text.ass,noise=alls=3:allf=t,fade=in:d=0.25,fade=out:st={total-0.4:.3f}:d=0.4",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", f"renders/shorts/{clip}.mp4"], check=True)
