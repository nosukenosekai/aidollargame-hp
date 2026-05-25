#!/usr/bin/env python3
"""
OGP画像ジェネレーター
- サイズ: 1200 x 630 px
- デザイン: サマーウォーズ調 (navy + cyan/blue + red accent)
"""
from PIL import Image, ImageDraw, ImageFont
import os

WIDTH, HEIGHT = 1200, 630
NAVY = (10, 18, 56)
NAVY2 = (18, 26, 74)
CYAN = (0, 216, 255)
BLUE = (26, 109, 255)
RED = (255, 87, 87)
WHITE = (255, 255, 255)
MUTED = (154, 168, 208)

FONT_REGULAR = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"
FONT_BOLD = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
FONT_BLACK = "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"
if not os.path.exists(FONT_BLACK):
    FONT_BLACK = FONT_BOLD

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

CLOSING_PUNCT = set("」』）】〕》〉、。，．・：；？！ヽヾゝゞ々ーぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮ〜‥…)]}")
OPENING_PUNCT = set("「『（【〔《〈([{")


def make_background():
    img = Image.new("RGB", (WIDTH, HEIGHT), NAVY)
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(NAVY[0] * (1 - t) + NAVY2[0] * t)
        g = int(NAVY[1] * (1 - t) + NAVY2[1] * t)
        b = int(NAVY[2] * (1 - t) + NAVY2[2] * t)
        ImageDraw.Draw(img).line([(0, y), (WIDTH, y)], fill=(r, g, b))
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for i in range(20):
        alpha = int(40 - i * 1.8)
        if alpha <= 0:
            break
        radius = 380 - i * 14
        cx, cy = WIDTH - 100, 80
        gd.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                   fill=(0, 216, 255, alpha))
    for i in range(20):
        alpha = int(40 - i * 1.8)
        if alpha <= 0:
            break
        radius = 420 - i * 16
        cx, cy = 80, HEIGHT - 60
        gd.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                   fill=(26, 109, 255, alpha))
    img.paste(glow, (0, 0), glow)
    return img


def draw_logo(draw, x=60, y=50):
    font = ImageFont.truetype(FONT_BOLD, 36)
    draw.text((x, y), "AI", font=font, fill=CYAN)
    ai_w = draw.textlength("AI", font=font)
    draw.text((x + ai_w, y), "dollargame", font=font, fill=WHITE)
    small_font = ImageFont.truetype(FONT_REGULAR, 16)
    draw.text((x, y + 48), "AI × DOLLAR × GAME", font=small_font, fill=MUTED)


def draw_accent_line(draw):
    bar_x = 60
    bar_y1 = 220
    bar_y2 = HEIGHT - 110
    for y in range(bar_y1, bar_y2):
        t = (y - bar_y1) / (bar_y2 - bar_y1)
        r = int(CYAN[0] * (1 - t) + BLUE[0] * t)
        g = int(CYAN[1] * (1 - t) + BLUE[1] * t)
        b = int(CYAN[2] * (1 - t) + BLUE[2] * t)
        draw.line([(bar_x, y), (bar_x + 4, y)], fill=(r, g, b))


def draw_url(draw):
    font = ImageFont.truetype(FONT_REGULAR, 22)
    url = "aidollargame.com"
    w = draw.textlength(url, font=font)
    draw.text((WIDTH - w - 60, HEIGHT - 60), url, font=font, fill=MUTED)
    dot_x = WIDTH - w - 60 - 18
    dot_y = HEIGHT - 55
    draw.ellipse([dot_x, dot_y, dot_x + 10, dot_y + 10], fill=RED)


def wrap_text(text, font, max_width, draw):
    lines = []
    current = ""
    i = 0
    while i < len(text):
        ch = text[i]
        test = current + ch
        if draw.textlength(test, font=font) > max_width and current:
            if ch in CLOSING_PUNCT:
                current = test
                i += 1
                continue
            if current[-1] in OPENING_PUNCT and len(current) > 1:
                lines.append(current[:-1])
                current = current[-1] + ch
                i += 1
                continue
            lines.append(current)
            current = ch
        else:
            current = test
        i += 1
    if current:
        lines.append(current)
    return lines


def render_card(title, subtitle, output_filename, title_size=64, sub_size=28):
    img = make_background()
    draw = ImageDraw.Draw(img)
    draw_logo(draw)
    draw_accent_line(draw)
    draw_url(draw)
    title_font = ImageFont.truetype(FONT_BLACK, title_size)
    sub_font = ImageFont.truetype(FONT_REGULAR, sub_size)
    max_width = WIDTH - 180
    lines = wrap_text(title, title_font, max_width, draw)
    while len(lines) > 3 and title_size > 40:
        title_size -= 6
        title_font = ImageFont.truetype(FONT_BLACK, title_size)
        lines = wrap_text(title, title_font, max_width, draw)
    line_height = int(title_size * 1.35)
    total_h = line_height * len(lines)
    if subtitle:
        total_h += int(sub_size * 1.5) + 24
    y = (HEIGHT - total_h) // 2 + 30
    for line in lines:
        draw.text((90, y), line, font=title_font, fill=WHITE)
        y += line_height
    if subtitle:
        y += 24
        draw.text((90, y), subtitle, font=sub_font, fill=CYAN)
    path = os.path.join(OUTPUT_DIR, output_filename)
    img.save(path, "PNG", optimize=True)
    print(f"  ✓ {output_filename}  ({os.path.getsize(path) // 1024} KB)")


def main():
    print("Generating OGP images...")
    # TOP
    render_card("AIdollargame", "作業はAIに、愛は人間に。",
                "og-default.png", title_size=104, sub_size=36)
    # Product LPs
    render_card("AIside（アイサイド）", "ずっとそばにいる、あなたの付き人AI",
                "og-aiside.png", title_size=80)
    render_card("AIwill", "あなたの判断と意志を、デジタルに残す",
                "og-human-clone-ai.png", title_size=104)
    render_card("SNS AIエージェント", "LINEに、AIの接客を。",
                "og-line-ai-agent.png", title_size=80)
    # Articles
    render_card("2026年、AIを入れない会社が直面するリスク",
                "INSIGHT — 様子見ではもう遅い",
                "og-articles-ai-adoption-now.png", title_size=56)
    render_card("AIが役割を引き受けるとき、人間は何を手に入れるか",
                "FUTURE — 働き方の次の姿",
                "og-articles-ai-and-future.png", title_size=50)
    render_card("「作業はAIに、愛は人間に」の本当の意味",
                "PHILOSOPHY",
                "og-articles-ai-frees-humans.png", title_size=58)
    render_card("AIside — 「もう一人の自分」が時間を変える",
                "PRODUCT",
                "og-articles-aiside.png", title_size=60)
    render_card("AIwill — 社長の思考をAIに移植する理由",
                "PRODUCT",
                "og-articles-aiwill.png", title_size=58)
    render_card("LINE公式で満足してますか？",
                "SNS AIエージェントが変える顧客接点",
                "og-articles-sns-ai-agent.png", title_size=72)
    print("Done.")


if __name__ == "__main__":
    main()
