"""Procedural studio backdrop: dark blue-charcoal with warm out-of-focus lights
(a nod to the book's tunnel-lights story). One image per speaker, mirrored,
with a soft glow behind each head for separation."""
import numpy as np
from PIL import Image, ImageFilter

def backdrop(W, H, glow, mirror, seed=7):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = x / W, y / H
    top, bot = np.array([10, 14, 20]), np.array([20, 26, 34])
    img = top[None, None] * (1 - v[..., None]) + bot[None, None] * v[..., None]

    # soft warm glow behind the head
    gx, gy = glow
    d = np.sqrt(((u - gx) * W / H) ** 2 + (v - gy) ** 2)
    img += np.array([52, 36, 20])[None, None] * np.exp(-(d / 0.33) ** 2)[..., None]

    # bokeh lights, kept away from the centre where the person sits
    rng = np.random.default_rng(seed)
    layer = Image.new("RGB", (W, H))
    from PIL import ImageDraw
    dr = ImageDraw.Draw(layer)
    s = W / 1920
    for _ in range(24):
        while True:
            cx, cy = rng.uniform(0, 1), rng.uniform(0.02, 0.75)
            if abs(cx - 0.5) > 0.22 or cy < 0.12:
                break
        if mirror:
            cx = 1 - cx
        r = rng.uniform(25, 130) * s
        warm = rng.uniform(0.7, 1)
        col = np.array([255, 190, 110]) * warm + np.array([200, 215, 235]) * (1 - warm)
        a = rng.uniform(0.03, 0.11)
        c = tuple(int(k * a) for k in col)
        dr.ellipse([cx * W - r, cy * H - r, cx * W + r, cy * H + r], fill=c)
    layer = layer.filter(ImageFilter.GaussianBlur(14 * s))
    img += np.asarray(layer, np.float32)

    # vignette
    vd = np.sqrt(((u - 0.5) * 1.2) ** 2 + (v - 0.45) ** 2)
    img *= (1 - 0.55 * np.clip(vd - 0.25, 0, 1) ** 1.2)[..., None]
    img = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    return img.filter(ImageFilter.GaussianBlur(1.5 * s))

backdrop(2560, 1440, (0.5, 0.36), False).save("assets/bg_milad.png")
backdrop(1920, 1080, (0.515, 0.52), True).save("assets/bg_hooman.png")
print("ok")
