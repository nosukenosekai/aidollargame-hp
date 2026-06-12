#!/usr/bin/env python3
"""OGP image generator for AIdollargame HP (1200x630).

Cross-platform: uses bundled Linux fonts (IPAGothic / Liberation Sans) when the
macOS Hiragino fonts are absent, so it runs in CI as well as locally. Composites
the real brand mark (favicon-512.png) into every card and generates one unique
OG image per article from articles/_articles_index.json — so each page gets its
own first-party image instead of all sharing og-default.png."""

import os, re
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1200, 630
NAVY, NAVY2 = (10, 18, 56), (18, 26, 74)
CYAN, BLUE, RED = (0, 216, 255), (26, 109, 255), (255, 87, 87)
WHITE, MUTED = (255, 255, 255), (154, 168, 208)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ARTICLES_DIR = os.path.join(ROOT, "articles")
ICON_SRC = os.path.join(ROOT, "favicon-512.png")

# Font resolution: prefer macOS Hiragino (sharper), fall back to Linux fonts.
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
    """Brand mark with the white background knocked out to transparent."""
    im = Image.open(ICON_SRC).convert("RGBA")
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if r > 240 and g > 240 and b > 240:
                px[x, y] = (r, g, b, 0)
    return im.resize((size, size), Image.LANCZOS)


ICON = load_icon(72)


def make_background():
    img = Image.new("RGB", (WIDTH, HEIGHT), NAVY)
    d = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        t = y / HEIGHT
        d.line([(0, y), (WIDTH, y)],
               fill=tuple(int(NAVY[i] * (1 - t) + NAVY2[i] * t) for i in range(3)))
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for cx, cy, col, r0, step in [(WIDTH - 100, 80, CYAN, 380, 14),
                                  (80, HEIGHT - 60, BLUE, 420, 16)]:
        for i in range(20):
            alpha = int(40 - i * 1.8)
            if alpha <= 0:
                break
            r = r0 - i * step
            gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*col, alpha))
    img.paste(glow, (0, 0), glow)
    return img


def draw_lockup(img, d):
    """Top-left brand lockup: real Ai icon + Aidollargame wordmark."""
    img.paste(ICON, (56, 44), ICON)
    d.text((140, 52), "Aidollargame", font=lat(34), fill=WHITE)
    d.text((142, 96), "AI × DOLLAR × GAME", font=jp(15), fill=MUTED)


def draw_accent(d):
    x, y1, y2 = 60, 200, HEIGHT - 110
    for y in range(y1, y2):
        t = (y - y1) / (y2 - y1)
        d.line([(x, y), (x + 4, y)],
               fill=tuple(int(CYAN[i] * (1 - t) + BLUE[i] * t) for i in range(3)))


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
    total = lh * len(lines) + (int(28 * 1.6) + 24 if subtitle else 0)
    y = (HEIGHT - total) // 2 + 26
    for ln in lines:
        # faux-bold: redraw with a thin stroke to thicken regular-weight JP font
        d.text((90, y), ln, font=f, fill=WHITE, stroke_width=1, stroke_fill=WHITE)
        y += lh
    if subtitle:
        y += 24
        d.text((90, y), subtitle, font=jp(26), fill=CYAN)
    img.save(os.path.join(ROOT, out), "PNG", optimize=True)
    print(f"  ✓ {out}")


def render_default():
    img = make_background()
    d = ImageDraw.Draw(img)
    draw_lockup(img, d)
    draw_accent(d)
    draw_url(d)
    d.text((90, 250), "Aidollargame", font=lat(96), fill=WHITE)
    d.text((92, 392), "楽じゃなく、楽しいを考える。", font=jp(36),
           fill=CYAN, stroke_width=1, stroke_fill=CYAN)
    img.save(os.path.join(ROOT, "og-default.png"), "PNG", optimize=True)
    print("  ✓ og-default.png")


# Subtitle / sizing hints for the fixed (non-article) pages.
PRODUCTS = [
    ("AIside（アイサイド）", "ずっとそばにいる、あなたの付き人AI", "og-aiside.png", 80),
    ("AIwill", "経営者の判断と意志を、AIに残す", "og-human-clone-ai.png", 104),
    ("SNS AIエージェント", "LINEに、AIの接客を。", "og-line-ai-agent.png", 80),
]


def article_title(path):
    """Headline for an article file (from <h1>, falling back to <title>)."""
    t = open(path, encoding="utf-8").read()
    m = re.search(r"<h1>(.*?)</h1>", t, re.S) or re.search(r"<title>(.*?)</title>", t, re.S)
    if not m:
        return None
    title = re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return re.sub(r"\s*\|\s*AIdollargame\s*$", "", title)


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
