#!/usr/bin/env python3
"""明るい編集誌調のOG画像ジェネレーター（紙色ベース・2026-07-14 新設）
旧 generate_ogp.py の暗いネイビー×シアン調は封印。こちらを使う。
- サイズ 1200x630
- 紙色 #f5f4f0 / 黒 #101218 / 青 #2563eb / 黄マーカー / 赤ハート
"""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1200, 630
PAPER = (245, 244, 240)
INK = (16, 18, 24)
BLUE = (37, 99, 235)
YELLOW = (255, 214, 92)
RED = (255, 87, 87)
LINE = (223, 221, 214)
MUTED = (110, 112, 118)

FONT_BLACK = "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"
FONT_BOLD = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
FONT_MED = "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc"
if not os.path.exists(FONT_BLACK):
    FONT_BLACK = FONT_BOLD

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def base():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    # 上下の細い罫線（編集誌の版面）
    d.line([(80, 96), (W - 80, 96)], fill=LINE, width=2)
    d.line([(80, H - 96), (W - 80, H - 96)], fill=LINE, width=2)
    return img, d


def wordmark(d, x, y, size):
    """Aıdollargame — ı の上に赤ハート"""
    f = ImageFont.truetype(FONT_BLACK, size)
    d.text((x, y), "A", font=f, fill=INK)
    ix = x + d.textlength("A", font=f)
    d.text((ix, y), "ı", font=f, fill=INK)
    iw = d.textlength("ı", font=f)
    d.text((ix + iw, y), "dollargame", font=f, fill=INK)
    # heart dot
    cx, cy, s = ix + iw / 2, y + size * 0.24, size * 0.30
    rr = s / 4
    d.ellipse([cx - s / 2, cy - rr, cx, cy + rr], fill=RED)
    d.ellipse([cx, cy - rr, cx + s / 2, cy + rr], fill=RED)
    d.polygon([(cx - s / 2 + 1, cy), (cx + s / 2 - 1, cy), (cx, cy + s * 0.62)], fill=RED)


def url(d):
    f = ImageFont.truetype(FONT_MED, 22)
    t = "aidollargame.com"
    w = d.textlength(t, font=f)
    d.text((W - 80 - w, H - 84), t, font=f, fill=MUTED)
    d.ellipse([W - 80 - w - 20, H - 79, W - 80 - w - 10, H - 69], fill=RED)


def render_default():
    """トップ用: 明るい紙色にブランドスローガン。楽しい に黄色マーカー"""
    img, d = base()
    wordmark(d, 80, 128, 40)
    d.text((82, 182), "AI × DOLLAR × GAME", font=ImageFont.truetype(FONT_MED, 18), fill=MUTED)

    f = ImageFont.truetype(FONT_BLACK, 92)
    y1, y2 = 268, 268 + 118
    d.text((80, y1), "楽ではなく、", font=f, fill=INK)
    # line2: 楽しい(マーカー) を考える。
    x = 80
    tanoshii = "楽しい"
    tw = d.textlength(tanoshii, font=f)
    # 黄色マーカー（文字の下2/3を覆う）
    mk_top = y2 + int(92 * 0.50)
    mk_bot = y2 + int(92 * 0.98)
    d.rectangle([x - 6, mk_top, x + tw + 6, mk_bot], fill=YELLOW)
    d.text((x, y2), tanoshii, font=f, fill=INK)
    d.text((x + tw, y2), "を考える。", font=f, fill=INK)

    url(d)
    p = os.path.join(OUT, "og-default.png")
    img.save(p, "PNG", optimize=True)
    print(f"  ✓ og-default.png (bright)  ({os.path.getsize(p)//1024} KB)")


if __name__ == "__main__":
    print("Generating BRIGHT OGP...")
    render_default()
