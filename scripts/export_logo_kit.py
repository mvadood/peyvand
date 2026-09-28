"""Export consistent logo variants from the native SVG master.

This renders vector artwork; it does not retouch the selected raster reference.
Run: .venv/bin/python scripts/export_logo_kit.py
"""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "assets/branding/master/peyvand-logo-master.svg"
KIT = ROOT / "assets/branding/logo-kit"
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
DARK, LIGHT = "#15181B", "#E9ECEF"
IDS = ("stroke-left", "stroke-right", "wordmark")
RENDERER = shutil.which("rsvg-convert")


def element(tag, **attrs):
    return ET.Element(f"{{{SVG_NS}}}{tag}", {k.replace("_", "-"): str(v) for k, v in attrs.items()})


def groups(ids):
    source = ET.parse(MASTER).getroot()
    return [copy.deepcopy(g) for g in source.findall(f"{{{SVG_NS}}}g") if g.get("id") in ids]


def bounds(ids):
    data = json.loads((MASTER.parent / "geometry-validation.json").read_text())
    boxes = [c["bounds"] for c in data["contours"] if c["group"] in ids]
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def padded_box(box, pad):
    x0, y0, x1, y1 = box
    return (x0 - pad, y0 - pad, x1 - x0 + 2 * pad, y1 - y0 + 2 * pad)


def save_svg(path, ids, colour, viewbox, size=None, background=None, title="پیوند"):
    x, y, w, h = viewbox
    size = size or (round(w), round(h))
    root = element("svg", width=size[0], height=size[1], viewBox=f"{x:.4f} {y:.4f} {w:.4f} {h:.4f}", fill=colour, role="img")
    ET.SubElement(root, f"{{{SVG_NS}}}title").text = title
    if background:
        root.append(element("rect", x=x, y=y, width=w, height=h, fill=background))
    root.extend(groups(ids))
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    return path


def render(svg, png, width=None, height=None):
    if not RENDERER:
        raise RuntimeError("rsvg-convert is required to render SVG exports")
    command = [RENDERER, str(svg), "--output", str(png)]
    if width:
        command += ["--width", str(width)]
    if height:
        command += ["--height", str(height)]
    png.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(command, check=True)


def add_preview_art(root, ids, colour, dest, background, circle=False):
    x, y, w, h = dest
    root.append(element("rect", x=x, y=y, width=w, height=h, rx=18, fill=background))
    if circle:
        root.append(element("circle", cx=x + w / 2, cy=y + h / 2, r=min(w, h) * .42,
                            fill="none", stroke="#858D94", stroke_width=1.5, stroke_dasharray="5 7"))
    box = bounds(ids)
    if circle:
        bx, by, bw, bh = AVATAR_BOX
        scale = min(w, h) * .84 / bw
        tx, ty = x + w / 2 - (bx + bw / 2) * scale, y + h / 2 - (by + bh / 2) * scale
    else:
        bw, bh = box[2] - box[0], box[3] - box[1]
        scale = min(w * .77 / bw, h * .84 / bh)
        tx, ty = x + (w - bw * scale) / 2 - box[0] * scale, y + (h - bh * scale) / 2 - box[1] * scale
    outer = element("g", transform=f"translate({tx:.5f} {ty:.5f}) scale({scale:.7f})", fill=colour)
    for index, group in enumerate(groups(ids)):
        for node in group.iter():
            if node.get("id"):
                node.set("id", f"preview-{x}-{y}-{index}-{node.get('id')}")
        outer.append(group)
    root.append(outer)


def preview():
    root = element("svg", width=1800, height=1320, viewBox="0 0 1800 1320")
    root.append(element("rect", width=1800, height=1320, fill="#F7F8FA"))
    title = element("text", x=60, y=62, fill=DARK, font_family="sans-serif", font_size=30, font_weight=700)
    title.text = "PEYVAND / LOGO KIT"
    root.append(title)
    subtitle = element("text", x=60, y=97, fill="#59636C", font_family="sans-serif", font_size=19)
    subtitle.text = "Selected geometry · Persian wordmark · Two-colour identity"
    root.append(subtitle)
    cards = [
        (IDS, DARK, LIGHT, "Full logo / dark ink", False),
        (IDS, LIGHT, DARK, "Full logo / light ink", False),
        (IDS[:2], DARK, LIGHT, "Symbol only", False),
        (IDS[:2], DARK, LIGHT, "Avatar / light background", True),
        (IDS[:2], LIGHT, DARK, "Avatar / dark background", True),
        (("wordmark",), DARK, LIGHT, "Persian wordmark only", False),
    ]
    for i, (ids, colour, bg, label, circle) in enumerate(cards):
        x, y = 60 + (i % 3) * 570, 130 + (i // 3) * 585
        add_preview_art(root, ids, colour, (x, y, 540, 515), bg, circle)
        text = element("text", x=x, y=y + 548, fill=DARK, font_family="sans-serif", font_size=20)
        text.text = label
        root.append(text)
    path = KIT / "preview.svg"
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    render(path, KIT / "preview.png")


SYMBOL = bounds(IDS[:2])
WORDMARK = bounds(("wordmark",))
cx, cy = (SYMBOL[0] + SYMBOL[2]) / 2, (SYMBOL[1] + SYMBOL[3]) / 2
# Measure the actual vector-rendered contour so the square avatar does not
# acquire excess margin from empty corners of the symbol's bounding box.
master_alpha = np.array(Image.open(MASTER.parent / "peyvand-logo-master-validation.png"))[:, :, 3]
symbol_cutoff = (SYMBOL[3] + WORDMARK[1]) / 2
yy, xx = np.where((master_alpha >= 128) & (np.arange(master_alpha.shape[0])[:, None] < symbol_cutoff))
radius = float(np.max(np.hypot(xx + .5 - cx, yy + .5 - cy)))
avatar_side = float(2 * radius / .82)
AVATAR_BOX = (cx - avatar_side / 2, cy - avatar_side / 2, avatar_side, avatar_side)


def main():
    KIT.mkdir(parents=True, exist_ok=True)
    (KIT / "master").mkdir(exist_ok=True)
    shutil.copy2(MASTER, KIT / "master" / MASTER.name)
    shutil.copy2(MASTER.parent / "geometry-validation.json", KIT / "master/geometry-validation.json")
    variants = [
        ("logo", IDS, (0, 0, 1086, 1448), [("1086", 1086), ("2172", 2172)]),
        ("symbol", IDS[:2], padded_box(SYMBOL, 55), [("1024", 1024), ("256", 256)]),
        ("wordmark", ("wordmark",), padded_box(WORDMARK, 28), [("1600", 1600)]),
    ]
    for name, ids, box, sizes in variants:
        for ink, colour in (("dark", DARK), ("light", LIGHT)):
            stem = f"peyvand-{name}-{ink}-ink"
            svg = save_svg(KIT / "svg" / f"{stem}.svg", ids, colour, box)
            for label, width in sizes:
                render(svg, KIT / "png" / f"{stem}-{label}.png", width=width)
    for bg_name, background, colour in (("light", LIGHT, DARK), ("dark", DARK, LIGHT)):
        svg = save_svg(KIT / "avatars" / f"peyvand-avatar-{bg_name}-bg.svg", IDS[:2], colour,
                       AVATAR_BOX, size=(1024, 1024), background=background)
        render(svg, svg.with_suffix(".png"), width=1024, height=1024)
    for name in IDS:
        save_svg(KIT / "motion" / f"{name}.svg", (name,), DARK, (0, 0, 1086, 1448))
    preview()
    verify()
    archive = KIT.parent / "peyvand-logo-kit.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as package:
        for path in sorted(KIT.rglob("*")):
            if path.is_file():
                package.write(path, Path("peyvand-logo-kit") / path.relative_to(KIT))
    print(f"Packaged {archive.relative_to(ROOT)}")


def verify():
    checks = {}
    pairs = []
    for dark in sorted((KIT / "png").glob("*-dark-ink-*.png")):
        light = dark.with_name(dark.name.replace("-dark-ink-", "-light-ink-"))
        a, b = Image.open(dark), Image.open(light)
        assert a.mode == b.mode == "RGBA", (dark, a.mode, b.mode)
        aa, ab = np.array(a)[:, :, 3], np.array(b)[:, :, 3]
        assert a.size == b.size and np.array_equal(aa, ab), dark
        assert aa.min() == 0 and aa.max() == 255, dark
        assert all(aa[y, x] == 0 for x, y in ((0, 0), (-1, 0), (0, -1), (-1, -1)))
        assert np.any((aa > 0) & (aa < 255)), "Missing antialiased edges"
        for path, im, expected in ((dark, a, (21, 24, 27)), (light, b, (233, 236, 239))):
            pixels = np.array(im)
            assert np.all(pixels[:, :, :3][pixels[:, :, 3] == 255] == expected), path
        pairs.append({"dark": str(dark.relative_to(KIT)), "light": str(light.relative_to(KIT)), "size": list(a.size), "identical_alpha": True})
    checks["transparent_pairs"] = pairs
    full = np.array(Image.open(KIT / "png/peyvand-logo-dark-ink-1086.png"))[:, :, 3]
    count, labels, stats, _ = cv2.connectedComponentsWithStats((full >= 128).astype(np.uint8), 8)
    assert count - 1 == 10, f"Expected 2 strokes, 2 letter groups and 6 dots; found {count - 1}"
    assert full[1235, 547] == 0, "Persian letter counter filled"
    checks["connected_components"] = count - 1
    checks["persian_counter_transparent"] = True
    checks["avatar_circle_clearance"] = {}
    for name, bg in (("light", np.array([233, 236, 239])), ("dark", np.array([21, 24, 27]))):
        pixels = np.array(Image.open(KIT / f"avatars/peyvand-avatar-{name}-bg.png").convert("RGB"))
        yy, xx = np.where(np.max(np.abs(pixels.astype(int) - bg), axis=2) > 20)
        max_radius = float(np.max(np.hypot(xx + .5 - 512, yy + .5 - 512)))
        assert max_radius < 512 * .85
        checks["avatar_circle_clearance"][name] = {"max_ink_radius_px": round(max_radius, 2), "circle_radius_px": 512, "clearance_px": round(512 - max_radius, 2)}
    for svg in list((KIT / "svg").glob("*.svg")) + list((KIT / "motion").glob("*.svg")):
        root = ET.parse(svg).getroot()
        assert not root.findall(f".//{{{SVG_NS}}}image")
        assert not root.findall(f".//{{{SVG_NS}}}text")
    source = ET.parse(MASTER).getroot()
    for name in IDS:
        root = ET.parse(KIT / "motion" / f"{name}.svg").getroot()
        assert [float(v) for v in root.get("viewBox").split()] == [0, 0, 1086, 1448]
        extracted = root.find(f"{{{SVG_NS}}}g")
        # Compare attributes and path data rather than XML whitespace.
        a = [(p.get("d"), p.get("fill-rule")) for p in extracted.iter(f"{{{SVG_NS}}}path")]
        b = [(p.get("d"), p.get("fill-rule")) for p in source.find(f"{{{SVG_NS}}}g[@id='{name}']").iter(f"{{{SVG_NS}}}path")]
        assert a == b
    checks["motion_layers_identical_to_master"] = True
    checks["reference_sha256"] = hashlib.sha256((ROOT / "assets/branding/peyvand-logo.png").read_bytes()).hexdigest()
    checks["method"] = "All final variations are native SVG derivatives and direct rsvg-convert exports of one master. No raster retouching."
    (KIT / "validation.json").write_text(json.dumps(checks, indent=2) + "\n")
    inventory = []
    for path in sorted(KIT.rglob("*")):
        if path.suffix not in (".png", ".svg"):
            continue
        entry = {"file": str(path.relative_to(KIT)), "bytes": path.stat().st_size}
        if path.suffix == ".png":
            im = Image.open(path)
            entry.update(size=list(im.size), mode=im.mode)
        inventory.append(entry)
    (KIT / "manifest.json").write_text(json.dumps(inventory, indent=2) + "\n")
    print(f"Exported {len(inventory)} assets; transparency, geometry, Persian dots, avatars and layers verified.")


if __name__ == "__main__":
    main()
