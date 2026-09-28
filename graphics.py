"""Static graphics for the POC: road signs, tunnel interstitial, book card."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FA = "/System/Library/Fonts/SFArabic.ttf"
EN = "/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf"
BLUE, WHITE = (24, 74, 156), (255, 255, 255)


def fa(size, weight="Bold"):
    f = ImageFont.truetype(FA, size, layout_engine=ImageFont.Layout.RAQM)
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f


def text_w(d, s, f, **kw):
    b = d.textbbox((0, 0), s, font=f, **kw)
    return b[2] - b[0], b[3] - b[1], b


def sign(lines_fa, line_en=None, width=820, fa_size=60, pad=56):
    """Blue Iranian-style road sign with white inset border; returns RGBA with drop shadow."""
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    f_fa, f_en = fa(fa_size), ImageFont.truetype(EN, int(fa_size * 0.62))
    rows = []
    for s in lines_fa:
        w, h, b = text_w(tmp, s, f_fa, direction="rtl", language="fa")
        rows.append(("fa", s, f_fa, w, int(fa_size * 1.45), b))
    if line_en:
        w, h, b = text_w(tmp, line_en, f_en)
        rows.append(("en", line_en, f_en, w, int(fa_size * 1.0), b))
    width = max(width, max(r[3] for r in rows) + 2 * pad + 20)
    height = sum(r[4] for r in rows) + 2 * pad
    S = 40  # shadow margin
    img = Image.new("RGBA", (width + 2 * S, height + 2 * S), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([S + 6, S + 14, S + width + 6, S + height + 14], 34, fill=(0, 0, 0, 150))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(16)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([S, S, S + width, S + height], 34, fill=BLUE)
    d.rounded_rectangle([S + 14, S + 14, S + width - 14, S + height - 14], 24, outline=WHITE, width=7)
    y = S + pad
    for kind, s, f, w, lh, b in rows:
        x = S + (width - w) / 2 - b[0]
        ty = y + (lh - (b[3] - b[1])) / 2 - b[1]
        if kind == "fa":
            d.text((x, ty), s, font=f, fill=WHITE, direction="rtl", language="fa")
        else:
            d.text((x, ty), s, font=f, fill=(215, 228, 255))
        y += lh
    return img


def tunnel(W=1920, H=1080):
    """Night mountain road with a tunnel portal; returns (scene, headlights layer)."""
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    sky = np.array([10, 16, 32]) * (1 - y / H)[..., None] + np.array([34, 44, 70]) * (y / H)[..., None]
    img = Image.fromarray(sky.astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(3)
    for _ in range(140):  # stars
        sx, sy = rng.uniform(0, W), rng.uniform(0, H * 0.35)
        a = int(rng.uniform(60, 200))
        d.ellipse([sx, sy, sx + 2.4, sy + 2.4], fill=(255, 255, 255, a))
    # far and near mountains
    d.polygon([(0, 520), (260, 330), (520, 470), (820, 260), (1150, 430), (1450, 300), (1920, 480), (1920, 1080), (0, 1080)], fill=(22, 28, 42))
    d.polygon([(0, 640), (380, 420), (700, 360), (960, 330), (1240, 360), (1560, 440), (1920, 600), (1920, 1080), (0, 1080)], fill=(30, 36, 50))
    # portal
    cx, base, r = 960, 800, 250
    d.rectangle([cx - r - 70, base - r - 110, cx + r + 70, base], fill=(78, 80, 86))
    d.pieslice([cx - r - 40, base - r - 40 - r, cx + r + 40, base - r + 40 + r], 180, 360, fill=(96, 98, 104))
    d.rectangle([cx - r - 40, base - r, cx + r + 40, base], fill=(96, 98, 104))
    d.pieslice([cx - r, base - 2 * r, cx + r, base], 180, 360, fill=(6, 7, 10))
    d.rectangle([cx - r, base - r, cx + r, base], fill=(6, 7, 10))
    # road
    d.polygon([(cx - r + 10, base), (cx + r - 10, base), (1500, 1080), (420, 1080)], fill=(38, 40, 46))
    for i in range(6):
        t0, t1 = i / 6, i / 6 + 0.08
        yy0, yy1 = base + (1080 - base) * t0 ** 1.3, base + (1080 - base) * t1 ** 1.3
        w0, w1 = 3 + 10 * t0, 3 + 10 * t1
        d.polygon([(cx - w0, yy0), (cx + w0, yy0), (cx + w1, yy1), (cx - w1, yy1)], fill=(220, 190, 90))
    # headlights emerging from the tunnel
    hl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    for hx in (cx - 70, cx + 70):
        hd.ellipse([hx - 60, base - 95, hx + 60, base - 35], fill=(255, 236, 170, 110))
    hl = hl.filter(ImageFilter.GaussianBlur(26))
    core = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(core)
    for hx in (cx - 70, cx + 70):
        cd.ellipse([hx - 20, base - 78, hx + 20, base - 52], fill=(255, 250, 225, 255))
    hl = Image.alpha_composite(hl, core.filter(ImageFilter.GaussianBlur(3)))
    beam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(beam).polygon([(cx - 110, base - 60), (cx + 110, base - 60), (1380, 1080), (540, 1080)], fill=(255, 235, 170, 55))
    hl = Image.alpha_composite(beam.filter(ImageFilter.GaussianBlur(30)), hl)
    # the sign above the portal
    s = sign(["آیا چراغ‌هاتون روشنه؟"], "ARE YOUR LIGHTS ON?", width=700, fa_size=54, pad=40)
    img.alpha_composite(s, (cx - s.width // 2, base - r - 110 - s.height + 30))
    return img, hl


def book_card():
    """Typographic stand-in for the cover until a real cover image is added."""
    W, H = 520, 720
    img = Image.new("RGBA", (W + 80, H + 80), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([48, 56, W + 48, H + 56], fill=(0, 0, 0, 160))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(img)
    d.rectangle([40, 40, W + 40, H + 40], fill=(244, 206, 84))
    f = ImageFont.truetype(EN, 84)
    for i, w in enumerate(["ARE", "YOUR", "LIGHTS", "ON?"]):
        d.text((80, 90 + i * 96), w, font=f, fill=(30, 40, 90))
    f2 = ImageFont.truetype(EN, 30)
    d.text((80, 520), "How to Figure Out What", font=f2, fill=(30, 40, 90))
    d.text((80, 558), "the Problem Really Is", font=f2, fill=(30, 40, 90))
    d.text((80, 660), "GAUSE  &  WEINBERG", font=ImageFont.truetype(EN, 34), fill=(120, 60, 20))
    return img


if __name__ == "__main__":
    sign(["لطفاً چراغ‌ها را روشن کنید"], "PLEASE TURN ON YOUR LIGHTS").save("assets/sign1.png")
    sign(["لطفاً چراغ‌ها را خاموش کنید"], "PLEASE TURN OFF YOUR LIGHTS").save("assets/sign2.png")
    long = ["اگر روز است و چراغ‌هایتان روشن است، خاموششان کنید.",
            "اگر شب است و چراغ‌هایتان خاموش است، روشنشان کنید.",
            "اگر روز است و چراغ‌هایتان خاموش است، خاموش نگهشان دارید.",
            "اگر شب است و چراغ‌هایتان روشن است، روشن نگهشان دارید."]
    for i in range(1, 5):
        sign(long[:i], width=900, fa_size=34, pad=44).save(f"assets/sign3_{i}.png")
    scene, lights = tunnel()
    scene.save("assets/tunnel.png"); lights.save("assets/tunnel_lights.png")
    book_card().save("assets/book_card.png")
    print("ok")


def card(title_fa, lines_fa, en=None, width=900):
    """Dark rounded explainer card with amber title (for the vertical shorts)."""
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    f_t, f_l, f_e = fa(50), fa(46, "Semibold"), ImageFont.truetype(EN, 28)
    rows = [(title_fa, f_t, (255, 200, 90), 84)] + [(s, f_l, (255, 255, 255), 74) for s in lines_fa]
    h = 70 + sum(r[3] for r in rows) + (90 if en else 0)
    S = 40
    img = Image.new("RGBA", (width + 2 * S, h + 2 * S), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([S, S + 12, S + width, S + h + 12], 36, fill=(0, 0, 0, 160))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([S, S, S + width, S + h], 36, fill=(18, 24, 34, 235), outline=(255, 200, 90, 120), width=3)
    y = S + 40
    for s, f, col, lh in rows:
        w, _, b = text_w(tmp, s, f, direction="rtl", language="fa")
        d.text((S + (width - w) / 2 - b[0], y), s, font=f, fill=col, direction="rtl", language="fa")
        y += lh
    if en:
        for i, line in enumerate(en.split("\n")):
            w, _, b = text_w(tmp, line, f_e)
            d.text((S + (width - w) / 2 - b[0], y + 10 + i * 38), line, font=f_e, fill=(170, 180, 200))
    return img


def shorts_assets():
    sign(["پارکینگ پر است"], "PARKING FULL").save("assets/sign_parking_full.png")
    sign(["جای پارک رئیس دانشگاه"], "RESERVED - UNIVERSITY PRESIDENT").save("assets/sign_reserved.png")
    card("تعریف مسئله", ["تفاوتِ بین", "آنچه می‌خواهیم", "و آنچه درک می‌کنیم"],
         "A PROBLEM IS A DIFFERENCE BETWEEN\nTHINGS AS DESIRED AND THINGS AS PERCEIVED").save("assets/def_card.png")
    card("دو راه برای حل مسئله", ["۱. انتظارت رو تغییر بده"]).save("assets/ways_1.png")
    card("دو راه برای حل مسئله", ["۱. انتظارت رو تغییر بده", "۲. واقعیت رو تغییر بده"]).save("assets/ways_2.png")
