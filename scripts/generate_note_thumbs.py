from PIL import Image, ImageDraw, ImageFont

JP   = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
LAT  = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
NAVY, NAVY2 = (10,18,56), (22,34,90)
WHITE, RED, GREY = (255,255,255), (255,87,87), (180,188,215)
W, H = 1280, 670

def jp(s): return ImageFont.truetype(JP, s)
def lat(s): return ImageFont.truetype(LAT, s)

def icon_transparent(path, size):
    """favicon(白背景)を読み込み、白を透過にしてリサイズ"""
    im = Image.open(path).convert("RGBA")
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r,g,b,a = px[x,y]
            if r>240 and g>240 and b>240:
                px[x,y] = (r,g,b,0)
    return im.resize((size,size), Image.LANCZOS)

ICON = icon_transparent("favicon-512.png", 84)

def wrap(d, text, fnt, max_w):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur); cur=""; continue
        if d.textlength(cur+ch, font=fnt) <= max_w: cur += ch
        else: lines.append(cur); cur = ch
    if cur: lines.append(cur)
    return lines

def make(path, title, tag="楽じゃなく、楽しいを考える。", tsz=70):
    img = Image.new("RGB", (W,H), NAVY)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t=y/H; d.line([(0,y),(W,y)], fill=tuple(int(NAVY[i]+(NAVY2[i]-NAVY[i])*t) for i in range(3)))
    pad = 80
    # brand lockup: icon + wordmark
    img.paste(ICON, (pad, 48), ICON)
    d.text((pad+100, 72), "Aidollargame", font=lat(40), fill=WHITE)
    # accent bar
    d.rectangle([pad, 185, pad+90, 193], fill=RED)
    # title
    f = jp(tsz)
    lines = wrap(d, title, f, W-pad*2)
    y = 235
    for ln in lines:
        d.text((pad, y), ln, font=f, fill=WHITE); y += int(tsz*1.45)
    d.text((pad, H-88), tag, font=jp(30), fill=GREY)
    img.save(path, "PNG"); print("saved", path)

base = "content/note/images/"
make(base+"thumb-ai-built-site.png", "コードが書けない私が、\nAIだけでサイトを作り変えた")
make(base+"thumb-products.png",      "私たちが作る3つのAIと、\nそこに込めた「想い」")
make(base+"thumb-first-task.png",    "中小企業のAI、\n最初の1業務はこう選ぶ")
