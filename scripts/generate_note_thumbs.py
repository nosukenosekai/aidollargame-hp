#!/usr/bin/env python3
"""note thumbnail generator (1280x670) — light theme matching the OG images."""
from PIL import Image, ImageDraw, ImageFont
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
JP  = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
LAT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
BG_TOP, BG_BOT = (255, 255, 255), (236, 240, 248)
INK, RED, MUTED = (12, 20, 58), (255, 87, 87), (122, 134, 166)
W, H = 1280, 670


def jp(s):  return ImageFont.truetype(JP, s)
def lat(s): return ImageFont.truetype(LAT, s)


def load_icon(size):
    im = Image.open(os.path.join(ROOT, "favicon-512.png")).convert("RGBA")
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if r > 240 and g > 240 and b > 240:
                px[x, y] = (r, g, b, 0)
    return im.resize((size, size), Image.LANCZOS)


ICON = load_icon(80)


def wrap(d, text, fnt, max_w):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        if d.textlength(cur + ch, font=fnt) <= max_w:
            cur += ch
        else:
            lines.append(cur); cur = ch
    if cur:
        lines.append(cur)
    return lines


def make(path, title, tag="楽じゃなく、楽しいを考える。", tsz=70):
    img = Image.new("RGB", (W, H), BG_TOP)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)],
               fill=tuple(int(BG_TOP[i] * (1 - t) + BG_BOT[i] * t) for i in range(3)))
    pad = 80
    img.paste(ICON, (pad, 44), ICON)
    d.text((pad + 100, 52), "Aidollargame", font=lat(40), fill=INK)
    d.text((pad + 102, 100), "AI × DOLLAR × GAME", font=jp(16), fill=MUTED)
    d.rectangle([pad, 200, pad + 90, 209], fill=RED)
    f = jp(tsz)
    y = 250
    for ln in wrap(d, title, f, W - pad * 2):
        d.text((pad, y), ln, font=f, fill=INK, stroke_width=1, stroke_fill=INK)
        y += int(tsz * 1.45)
    d.text((pad, H - 88), tag, font=jp(30), fill=MUTED)
    img.save(os.path.join(ROOT, path), "PNG")
    print("saved", path)


if __name__ == "__main__":
    base = "content/note/images/"
    make(base + "thumb-ai-built-site.png", "コードが書けない私が、\nAIだけでサイトを作り変えた")
    make(base + "thumb-products.png",      "私たちが作る3つのAIと、\nそこに込めた「想い」")
    make(base + "thumb-first-task.png",    "中小企業のAI、\n最初の1業務はこう選ぶ")
    make(base + "thumb-ai-terms.png",      "AI用語、ぜんぶ\n「たとえ話」で説明します")
    make(base + "thumb-worldcup.png",      "「強い」と「勝つ」は違う\nそれでも優勝はスペイン", tsz=60)
