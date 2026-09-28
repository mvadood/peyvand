"""Cover (9:16, Reels/Shorts) and thumbnail (16:9, YouTube) for the parking clip."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = "assets/branding/layout-v2/fonts/Vazirmatn-Bold.ttf"
LOGO = "assets/branding/logo-kit/png/peyvand-logo-light-ink-1086.png"
NAVY, AMBER, WHITE, GREY = (22, 35, 59), (242, 184, 75), (255, 255, 255), (190, 198, 210)
TITLE = [("جای پارکِ", WHITE), ("رئیس دانشگاه", AMBER), ("رو گرفتن!", WHITE)]
SUB = "یه ترفند ساده برای حل مسئله"


def f(size):
    return ImageFont.truetype(FONT, size, layout_engine=ImageFont.Layout.RAQM)


def bbox(d, s, fnt):
    return d.textbbox((0, 0), s, font=fnt, direction="rtl", language="fa")


def boxed_line(img, s, fnt, color, cx=None, right=None, cy=0, pad=(28, 14), box=NAVY):
    d = ImageDraw.Draw(img)
    b = bbox(d, s, fnt)
    w, h = b[2] - b[0], b[3] - b[1]
    x = (cx - w / 2) if cx is not None else (right - w)
    y = cy - h / 2
    if box:
        d.rounded_rectangle([x - pad[0], y - pad[1], x + w + pad[0], y + h + pad[1] + 6], 14, fill=box)
    d.text((x - b[0], y - b[1]), s, font=fnt, fill=color, direction="rtl", language="fa")
    return h


def logo(img, cx, cy, height):
    lg = Image.open(LOGO).convert("RGBA")
    lg = lg.resize((int(lg.width * height / lg.height), height), Image.LANCZOS)
    img.alpha_composite(lg, (int(cx - lg.width / 2), int(cy - lg.height / 2)))


def vignette(img, strength=0.35):
    w, h = img.size
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((x - w / 2) / (w / 2)) ** 2 + ((y - h / 2) / (h / 2)) ** 2)
    k = 1 - strength * np.clip(r - 0.6, 0, 1)
    a = np.array(img.convert("RGB"), np.float32) * k[..., None]
    return Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert("RGBA")


def cover():
    bg = Image.open("assets/episodes/01/broll/b08_president.png").convert("RGB").resize((1080, 1920), Image.LANCZOS)
    img = vignette(bg.convert("RGBA"), 0.3)
    top = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(top).rectangle([0, 0, 1080, 300], fill=(0, 0, 0, 90))
    img.alpha_composite(top.filter(ImageFilter.GaussianBlur(60)))
    logo(img, 540, 140, 150)
    y = 470
    for s, c in TITLE:
        boxed_line(img, s, f(104), c, cx=540, cy=y, pad=(34, 18))
        y += 150
    boxed_line(img, SUB, f(46), GREY, cx=540, cy=y + 20, pad=(26, 12), box=(12, 19, 33))
    img.convert("RGB").save("renders/shorts/parking_v2_cover.jpg", quality=94)


def thumbnail():
    bg = Image.open("assets/episodes/01/broll/t01_president_16x9.png").convert("RGB").resize((1280, 720), Image.LANCZOS)
    img = bg.convert("RGBA")
    shade = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shade).rectangle([640, 0, 1280, 720], fill=(8, 12, 22, 110))
    img.alpha_composite(shade.filter(ImageFilter.GaussianBlur(80)))
    logo(img, 1195, 78, 104)
    y = 230
    sizes = [86, 96, 86]
    for (s, c), sz in zip(TITLE, sizes):
        boxed_line(img, s, f(sz), c, right=1215, cy=y, box=None)
        y += 118
    boxed_line(img, SUB, f(34), GREY, right=1215, cy=y + 6, box=None)
    img.convert("RGB").save("renders/shorts/parking_v2_thumbnail.jpg", quality=94)


if __name__ == "__main__":
    cover()
    thumbnail()
    print("ok")
