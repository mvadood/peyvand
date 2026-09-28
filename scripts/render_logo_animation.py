#!/usr/bin/env python3
"""Render the approved Peyvand SVG paths as a 2.8-second ident.

Requires rsvg-convert and FFmpeg. Run from any directory. No network calls.
The SVG master and approved logo kit are read-only inputs.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/branding/animation"
MASTER = ROOT / "assets/branding/master/peyvand-logo-master.svg"
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)
FPS, DURATION = 30, 2.8
FORMATS = {"landscape": (1920, 1080), "vertical": (1080, 1920)}
THEMES = {"light": ("#E9ECEF", "#15181B"), "dark": ("#15181B", "#E9ECEF")}
TIMELINE = {
    "stroke-left": dict(start=0.08, end=0.78, fade_end=0.28, dx=-130, dy=90, rotation=-5, cx=369, cy=471),
    "stroke-right": dict(start=0.36, end=1.06, fade_end=0.56, dx=130, dy=-90, rotation=5, cx=703, cy=739),
    "wordmark": dict(start=1.12, end=1.58, fade_end=1.58, dx=0, dy=24, rotation=0, cx=543, cy=1257),
}


def tool(name):
    found = shutil.which(name)
    if name in ("ffmpeg", "ffprobe"):
        full = Path("/opt/homebrew/opt/ffmpeg-full/bin") / name
        if full.exists():
            return str(full)
    if not found:
        raise RuntimeError(f"Required program not found: {name}")
    return found


def run(args, **kwargs):
    return subprocess.run([str(x) for x in args], check=True, **kwargs)


def ease(t, start, end):
    u = max(0.0, min(1.0, (t - start) / (end - start)))
    return 1 - (1 - u) ** 3


def frame(width, height, theme, seconds):
    bg, ink = THEMES[theme]
    root = ET.Element(f"{{{NS}}}svg", width=str(width), height=str(height), viewBox=f"0 0 {width} {height}")
    ET.SubElement(root, f"{{{NS}}}rect", width=str(width), height=str(height), fill=bg)
    # Fit visible artwork, not the original raster canvas; maintain original proportions.
    scale = min(width * 0.80 / 893.031, height * 0.80 / 1303.078)
    tx, ty = width / 2 - 542.235 * scale, height / 2 - 735.175 * scale
    placed = ET.SubElement(root, f"{{{NS}}}g", transform=f"translate({tx:.6f} {ty:.6f}) scale({scale:.9f})", fill=ink)
    for source in ET.parse(MASTER).getroot().findall(f"{{{NS}}}g"):
        group = copy.deepcopy(source)
        cue = TIMELINE[group.attrib["id"]]
        remaining = 1 - ease(seconds, cue["start"], cue["end"])
        group.set("opacity", f'{ease(seconds, cue["start"], cue["fade_end"]):.8f}')
        group.set("transform", f'translate({cue["dx"] * remaining:.6f} {cue["dy"] * remaining:.6f}) rotate({cue["rotation"] * remaining:.6f} {cue["cx"]} {cue["cy"]})')
        if remaining == 0:
            group.set("transform", "matrix(1 0 0 1 0 0)")
        placed.append(group)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def render_video(aspect, theme):
    w, h = FORMATS[aspect]
    destination = OUT / f"peyvand-intro-{aspect}-{theme}-silent.mp4"
    with tempfile.TemporaryDirectory(prefix="peyvand-motion-") as temporary:
        directory = Path(temporary)
        for index in range(round(FPS * DURATION)):
            run([tool("rsvg-convert"), "-o", directory / f"{index:04d}.png"], input=frame(w, h, theme, index / FPS))
        run([tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y", "-framerate", FPS,
             "-i", directory / "%04d.png", "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
             "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
             "-movflags", "+faststart", destination])
    poster = OUT / f"peyvand-intro-{aspect}-{theme}-poster.png"
    run([tool("rsvg-convert"), "-o", poster], input=frame(w, h, theme, DURATION))
    print(f"Rendered {destination.name}", flush=True)


def mux_audio():
    sound = OUT / "audio/peyvand-sonic-signature.wav"
    if not sound.exists():
        return
    for aspect in FORMATS:
        for theme in THEMES:
            stem = f"peyvand-intro-{aspect}-{theme}"
            run([tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y", "-i", OUT / f"{stem}-silent.mp4",
                 "-i", sound, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                 "-t", DURATION, "-movflags", "+faststart", OUT / f"{stem}.mp4"])


def prepare_audio():
    """Deterministic finishing of the retained generated take; no regeneration."""
    import array
    import math
    source = OUT / "audio/take-3.mp3"
    if not source.exists():
        return
    raw = run([tool("ffmpeg"), "-v", "error", "-i", source, "-f", "f32le", "-ac", "2", "-ar", "48000", "-"], capture_output=True).stdout
    samples = array.array("f", raw)
    if __import__("sys").byteorder != "little":
        samples.byteswap()
    peak = max(abs(x) for x in samples)
    gain = -4.5 - 20 * math.log10(peak)
    filters = f"volume={gain:.9f}dB,afade=t=in:d=0.01,afade=t=out:st=2.45:d=0.25,apad,atrim=duration=2.8"
    run([tool("ffmpeg"), "-v", "error", "-y", "-i", source, "-af", filters, "-ac", "2", "-ar", "48000", "-c:a", "pcm_s24le", OUT / "audio/peyvand-sonic-signature.wav"])


def verify():
    results = []
    for path in sorted(OUT.glob("*.mp4")):
        data = json.loads(run([tool("ffprobe"), "-v", "error", "-show_streams", "-show_format", "-of", "json", path], capture_output=True).stdout)
        video = next(x for x in data["streams"] if x["codec_type"] == "video")
        aspect = "landscape" if "landscape" in path.name else "vertical"
        assert (video["width"], video["height"]) == FORMATS[aspect]
        assert video["nb_frames"] == "84" and video["r_frame_rate"] == "30/1"
        assert abs(float(data["format"]["duration"]) - DURATION) < 0.04
        has_audio = any(x["codec_type"] == "audio" for x in data["streams"])
        assert has_audio == ("silent" not in path.name)
        run([tool("ffmpeg"), "-v", "error", "-i", path, "-f", "null", "-"], capture_output=True)
        results.append(dict(file=path.name, width=video["width"], height=video["height"], frames=84, fps=30, duration=2.8, audio=has_audio, decode="passed"))
    baseline = json.loads((ROOT / "assets/branding/approved-logo-kit.json").read_text())
    for record in baseline["files"]:
        path = ROOT / "assets/branding" / record["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"], path
    # Finished placement must contain every original path with identity component transforms.
    finished = ET.fromstring(frame(1920, 1080, "light", 2.0))
    original_paths = [(p.get("d"), p.get("fill-rule")) for p in ET.parse(MASTER).iter(f"{{{NS}}}path")]
    assert [(p.get("d"), p.get("fill-rule")) for p in finished.iter(f"{{{NS}}}path")] == original_paths
    for group in finished.findall(f".//{{{NS}}}g[@id]"):
        assert group.get("opacity") == "1.00000000"
        assert group.get("transform") == "matrix(1 0 0 1 0 0)"
    (OUT / "validation.json").write_text(json.dumps(dict(exports=results, approved_baseline_files_unchanged=len(baseline["files"]), native_path_geometry="identical", final_component_transforms="identity"), indent=2) + "\n")


def package():
    with zipfile.ZipFile(OUT.parent / "peyvand-animation-v1.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(OUT.rglob("*")):
            if path.is_file():
                archive.write(path, Path("peyvand-animation-v1") / path.relative_to(OUT))
        archive.write(Path(__file__), "peyvand-animation-v1/source/render_logo_animation.py")
        archive.write(MASTER, "peyvand-animation-v1/source/peyvand-logo-master.svg")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mux-only", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if not args.mux_only:
        (OUT / "timeline.json").write_text(json.dumps(dict(duration=DURATION, fps=FPS, ease="cubic-out", groups=TIMELINE), indent=2) + "\n")
        for aspect in FORMATS:
            for theme in THEMES:
                render_video(aspect, theme)
    prepare_audio()
    mux_audio()
    verify()
    package()


if __name__ == "__main__":
    main()
