#!/usr/bin/env python3
"""OGP image generator for AIdollargame HP (1200x630).

Light, brand-consistent cards: the logo is black-on-white by design, so a light
background keeps the mark crisp (a dark bg buries the black "A"). Cross-platform
fonts (IPAGothic / Liberation Sans) let it run in CI as well as locally. The
real brand mark (favicon-512.png) is composited into every card, and one unique
OG image is generated per article (scanned from articles/*.html) so each page
has its own first-party image instead of all sharing og-default.png."""

import os, re
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1200, 630
BG_TOP, BG_BOT = (255, 255, 255), (236, 240, 248)   # soft light gradient
INK = (12, 20, 58)                                   # near-navy text (readable)
RED = (255, 87, 87)                                  # brand accent (the heart)
MUTED = (122, 134, 166)
WHITE = (255, 255, 255)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ARTICLES_DIR = os.path.join(ROOT, "articles")
ICON_SRC = os.path.join(ROOT, "favicon-512.png")


def _first(paths, default):
    for p in paths:
        if os.path.exists(p):
            return p
    return default

JP_FONT = _first([
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
], "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf")
LAT_FONT = _first([
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
], JP_FONT)

CLOSING_PUNCT = set("」』）】〕》〉、。，．・：；？！ヽヾゝゞ々ーぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮ〜‥…)]}")
OPENING_PUNCT = set("「『（【〔《〈([{")


def jp(sz): return ImageFont.truetype(JP_FONT, sz)
def lat(sz): return ImageFont.truetype(LAT_FONT, sz)


def load_icon(size):
    """Brand mark with the white background knocked out to transparent so it
    sits cleanly on the light card (black A + red i/heart stay crisp)."""
    im = Image.open(ICON_SRC).convert("RGBA")
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if r > 240 and g > 240 and b > 240:
                px[x, y] = (r, g, b, 0)
    return im.resize((size, size), Image.LANCZOS)


ICON = load_icon(76)


def make_background():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_TOP)
    d = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        t = y / HEIGHT
        d.line([(0, y), (WIDTH, y)],
               fill=tuple(int(BG_TOP[i] * (1 - t) + BG_BOT[i] * t) for i in range(3)))
    return img


def draw_lockup(img, d):
    """Top-left brand lockup: real Ai icon + Aidollargame wordmark."""
    img.paste(ICON, (56, 44), ICON)
    d.text((144, 52), "Aidollargame", font=lat(34), fill=INK)
    d.text((146, 96), "AI × DOLLAR × GAME", font=jp(15), fill=MUTED)


def draw_accent(d):
    d.rectangle([60, 210, 150, 219], fill=RED)


def draw_url(d):
    f = jp(22)
    url = "aidollargame.com"
    w = d.textlength(url, font=f)
    d.text((WIDTH - w - 60, HEIGHT - 58), url, font=f, fill=MUTED)
    d.ellipse([WIDTH - w - 78, HEIGHT - 53, WIDTH - w - 68, HEIGHT - 43], fill=RED)


def wrap(text, font, max_w, d):
    lines, cur, i = [], "", 0
    while i < len(text):
        ch = text[i]
        if d.textlength(cur + ch, font=font) > max_w and cur:
            if ch in CLOSING_PUNCT:
                cur += ch; i += 1; continue
            if cur[-1] in OPENING_PUNCT and len(cur) > 1:
                lines.append(cur[:-1]); cur = cur[-1] + ch; i += 1; continue
            lines.append(cur); cur = ch
        else:
            cur += ch
        i += 1
    if cur:
        lines.append(cur)
    return lines


def render_card(title, subtitle, out, title_size=60):
    img = make_background()
    d = ImageDraw.Draw(img)
    draw_lockup(img, d)
    draw_accent(d)
    draw_url(d)
    max_w = WIDTH - 180
    f = jp(title_size)
    lines = wrap(title, f, max_w, d)
    while len(lines) > 3 and title_size > 40:
        title_size -= 6
        f = jp(title_size)
        lines = wrap(title, f, max_w, d)
    lh = int(title_size * 1.4)
    total = lh * len(lines) + (int(26 * 1.6) + 24 if subtitle else 0)
    y = (HEIGHT - total) // 2 + 26
    for ln in lines:
        # faux-bold: redraw with a thin matching stroke to thicken the JP font
        d.text((90, y), ln, font=f, fill=INK, stroke_width=1, stroke_fill=INK)
        y += lh
    if subtitle:
        y += 24
        d.text((90, y), subtitle, font=jp(26), fill=RED)
    img.save(os.path.join(ROOT, out), "PNG", optimize=True)
    print(f"  ✓ {out}")


def render_default():
    img = make_background()
    d = ImageDraw.Draw(img)
    draw_lockup(img, d)
    draw_accent(d)
    draw_url(d)
    d.text((90, 250), "Aidollargame", font=lat(96), fill=INK)
    d.text((92, 392), "楽じゃなく、楽しいを考える。", font=jp(36),
           fill=INK, stroke_width=1, stroke_fill=INK)
    img.save(os.path.join(ROOT, "og-default.png"), "PNG", optimize=True)
    print("  ✓ og-default.png")


PRODUCTS = [
    ("AIside（アイサイド）", "ずっとそばにいる、あなたの付き人AI", "og-aiside.png", 80),
    ("AIwill", "経営者の判断と意志を、AIに残す", "og-human-clone-ai.png", 104),
    ("SNS AIエージェント", "LINEに、AIの接客を。", "og-line-ai-agent.png", 80),
]


EMOJI_RE = re.compile(
    "[\U0001F1E6-\U0001F1FF\U0001F300-\U0001FAFF\U00002600-\U000027BF"
    "\U0000FE00-\U0000FE0F\U0001F000-\U0001F0FF\U000E0000-\U000E007F]+")


def article_title(path):
    """Headline for an article file (from <h1>, falling back to <title>).
    Emoji/flags are stripped — the OG font can't render them."""
    t = open(path, encoding="utf-8").read()
    m = re.search(r"<h1>(.*?)</h1>", t, re.S) or re.search(r"<title>(.*?)</title>", t, re.S)
    if not m:
        return None
    title = re.sub(r"<[^>]+>", "", m.group(1)).strip()
    title = re.sub(r"\s*\|\s*AIdollargame\s*$", "", title)
    title = EMOJI_RE.sub("", title)
    return re.sub(r"\s{2,}", " ", title).strip()


def main():
    print("Generating OGP images...")
    render_default()
    for title, sub, out, sz in PRODUCTS:
        render_card(title, sub, out, title_size=sz)

    # One unique OG image per article — scan the HTML so brand-new articles
    # (added by generate_articles.py in CI) are never missed.
    n = 0
    for fname in sorted(os.listdir(ARTICLES_DIR)):
        if not fname.endswith(".html") or fname == "index.html":
            continue
        slug = fname[:-5]
        title = article_title(os.path.join(ARTICLES_DIR, fname))
        if not title:
            continue
        render_card(title, "AIdollargame", f"og-articles-{slug}.png", title_size=54)
        n += 1
    print(f"Done. ({n} article images)")


if __name__ == "__main__":
    main()
