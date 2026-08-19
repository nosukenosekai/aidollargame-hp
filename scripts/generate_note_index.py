#!/usr/bin/env python3
"""公式note(note.com/aidollargame)の記事一覧を自社サイトの静的ページに書き出す。

なぜ静的HTMLで持つのか:
  トップページのnote表示はRSSをJavaScriptで取りに行っているため、
  クローラーからは空のグリッドにしか見えず、noteの記事が自社ドメインから
  1本もリンクされていないのと同じ状態になっていた。
  検索エンジンとAI検索に「この会社の記事」として拾わせるには、
  サーバーから返る時点でHTMLの中にタイトル・日付・要約・リンクが
  入っている必要がある。だから毎回ここで焼き込む。

出力:
  note.html            … 記事一覧ページ(sitemapとllms.txtにも登録する)
  sitemap.xml          … note.html の行を追加/更新
  llms.txt             … note記事の一覧をマーカー区間に差し込み
"""

import json
import re
import sys
import urllib.request
from datetime import datetime, timezone, timedelta
from html import escape
from pathlib import Path

REPO = Path(__file__).parent.parent
NOTE_USER = "aidollargame"
API = "https://note.com/api/v2/creators/{}/contents?kind=note&page={}"
SITE = "https://aidollargame.com"
JST = timezone(timedelta(hours=9))

# note記事と、同じ内容を自社サイトにも置いてある記事の対応。
# 両方向にリンクを張るためのもの。新しく対応をつけたらここに足す。
HP_COUNTERPART = {
    "n8934236c7a1f": ("articles/ai-built-my-site.html", "コードが書けない私が、AIだけで自社サイトを作り変えた話"),
    "n7888c888dc23": ("articles/token-capital.html", "マイクロソフトCEOの問い：AIに「仕事」は渡せても、学びは渡せない"),
    "nfd9c26d7fc23": ("articles/ai-jargon-analogies.html", "呪文みたいなAI用語を、ぜんぶ身近なものに例えてみた"),
    "nb4ed5df64f62": ("articles/ai-musical-chairs.html", "AI時代の椅子取りゲームは、もう始まっている"),
    "n29bd8b4acd64": ("articles/ai-job-loss-vs-shortage-2026.html", "「AIに仕事を奪われる」は本当か？"),
    "nf4c86cbd6660": ("articles/ai-roi-cases-2026.html", "AI導入が「利益・コスト・時間」に効いた実例10選"),
    "nd8c8aad2400c": ("articles/ai-training-evidence-2026.html", "AIで研修すると人は育つのか"),
    "nba5295a09b05": ("articles/ai-phone-seria-2026.html", "セリアが代表電話の約75%をAIに任せた"),
    "n4c7244ca59ee": ("articles/ai-scam-2026.html", "その電話、AIかもしれません"),
    "n121d1703a4c3": ("articles/ai-firm-survey-2026.html", "AIを使っている会社は69%、なのに9割が「変わっていない」"),
    "n2406b93d2880": ("articles/ai-skill-gap-2026.html", "AIで差は縮むのか、広がるのか"),
    "nfcaf9c186d8e": ("articles/ai-interview-2026.html", "AIに面接をやらせたら内定が12%増えた"),
    "n37843927e437": ("articles/ai-jobs-payroll-2026.html", "AIで雇用は減っていない。ただし22〜25歳の入口だけがへこんでいる"),
}

# 絵文字・記号の装飾は自社サイト側では出さない(サイト全体の表記ルール)。
EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF"
    "\U00002190-\U000021FF\U00002B00-\U00002BFF️⃣]"
)
TAG = re.compile(r"<[^>]+>")


def clean_text(s):
    s = EMOJI.sub("", s or "")
    s = s.replace("　", " ")
    return re.sub(r"\s+", " ", s).strip()


def fetch_all():
    items, page = [], 1
    while page <= 20:
        req = urllib.request.Request(
            API.format(NOTE_USER, page),
            headers={"User-Agent": "aidollargame-site-builder/1.0"},
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.load(r)["data"]
        items += data["contents"]
        if data.get("isLastPage"):
            break
        page += 1
    # 同じ記事が複数ページにまたがって返ることがあるのでkeyで一意にする
    uniq = {}
    for it in items:
        uniq[it["key"]] = it
    return sorted(uniq.values(), key=lambda x: x["publishAt"], reverse=True)


def excerpt(body, limit=110):
    t = clean_text(TAG.sub("", body or ""))
    if len(t) <= limit:
        return t
    cut = t[:limit]
    for sep in ("。", "、", " "):
        i = cut.rfind(sep)
        if i > limit * 0.5:
            return cut[: i + 1].rstrip("、 ")
    return cut + "…"


def card(it):
    key = it["key"]
    title = clean_text(it["name"])
    url = it.get("noteUrl") or "https://note.com/{}/n/{}".format(NOTE_USER, key)
    d = datetime.fromisoformat(it["publishAt"]).astimezone(JST)
    date_disp = d.strftime("%Y / %m / %d")
    img = it.get("eyecatch") or ""
    tags = [
        clean_text(h.get("hashtag", {}).get("name", "")).lstrip("#")
        for h in (it.get("hashtags") or [])
    ]
    tags = [t for t in tags if t][:3]
    label = "有料記事" if it.get("price") else (tags[0] if tags else "note")
    hp = HP_COUNTERPART.get(key)

    img_html = (
        '      <div class="card-image" style="background-image:url(\'{}\')"></div>\n'.format(escape(img))
        if img else ""
    )
    hp_html = ""
    if hp:
        hp_html = (
            '        <a class="card-hp" href="{}">自社サイトにも同じ話を書いています →</a>\n'
        ).format(escape(hp[0]))

    return (
        '    <article class="article-card note-card" data-note-key="{key}">\n'
        '      <div class="card-color-bar"></div>\n'
        "{img}"
        '      <div class="card-body">\n'
        '        <div class="card-tag">{label}</div>\n'
        '        <div class="card-date">{date}</div>\n'
        '        <h2 class="card-title">{title}</h2>\n'
        '        <p class="card-desc">{desc}</p>\n'
        '        <a class="card-link" href="{url}" target="_blank" rel="noopener">noteで読む →</a>\n'
        "{hp}"
        "      </div>\n"
        "    </article>\n"
    ).format(
        key=escape(key),
        img=img_html,
        label=escape(label),
        date=date_disp,
        title=escape(title),
        desc=escape(excerpt(it.get("body", ""))),
        url=escape(url),
        hp=hp_html,
    )


def build_html(items, css):
    newest = datetime.fromisoformat(items[0]["publishAt"]).astimezone(JST)
    cards = "".join(card(it) for it in items)

    itemlist = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "株式会社AIdollargame 公式note 記事一覧",
        "itemListOrder": "https://schema.org/ItemListOrderDescending",
        "numberOfItems": len(items),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "url": it.get("noteUrl") or "https://note.com/{}/n/{}".format(NOTE_USER, it["key"]),
                "name": clean_text(it["name"]),
            }
            for i, it in enumerate(items)
        ],
    }
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "ホーム", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "公式note 記事一覧", "item": SITE + "/note.html"},
        ],
    }
    desc = (
        "株式会社AIdollargameの公式note（note.com/aidollargame）に公開した記事{}本の一覧です。"
        "中小企業のAI導入、AI活用の実証研究、公的調査の読み解きなどを、出典つきで書いています。"
    ).format(len(items))

    return """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="favicon-32.png">
<link rel="apple-touch-icon" sizes="180x180" href="favicon-180.png">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>公式note 記事一覧 | 株式会社AIdollargame</title>
<meta name="description" content="{desc}">
<meta name="author" content="株式会社AIdollargame">
<meta name="theme-color" content="#0a1238">
<link rel="canonical" href="{site}/note.html">

<meta property="og:type" content="website">
<meta property="og:site_name" content="株式会社AIdollargame">
<meta property="og:title" content="公式note 記事一覧 | 株式会社AIdollargame">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{site}/note.html">
<meta property="og:image" content="{site}/og-default.png">
<meta property="og:locale" content="ja_JP">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="公式note 記事一覧 | 株式会社AIdollargame">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{site}/og-default.png">

<script type="application/ld+json">
{itemlist}
</script>
<script type="application/ld+json">
{breadcrumb}
</script>

{css}
<style>
/* note一覧ページの上書き。カードは<a>ではなく<article>なので、
   リンクを2本(note本体 / 自社サイト版)持てるようにしている。 */
  .note-card {{ display:flex; flex-direction:column; }}
  .note-card .card-title {{ font-size:1.15rem; line-height:1.6; margin:0; }}
  .note-card .card-desc {{ font-size:0.98rem; line-height:1.95; margin:0; }}
  .note-card .card-link {{ display:block; text-decoration:none; font-size:0.8rem; }}
  .note-card .card-hp {{ display:block; margin-top:0.5rem; font-size:0.8rem; text-decoration:underline; text-underline-offset:3px; opacity:0.75; }}
  .note-lead {{ max-width:760px; }}
  .note-lead p {{ font-size:1.05rem; line-height:2.1; }}
  .note-follow {{ display:inline-block; margin-top:1.6rem; padding:0.9rem 1.6rem; border:1px solid #000; border-radius:6px; text-decoration:none; font-size:0.95rem; font-weight:700; }}
  .note-follow:hover {{ background:#000 !important; color:#fff !important; }}
</style>
<!-- Cloudflare Web Analytics --><script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token": "f2249d4d1b044fc1a67981c0f896d861"}}'></script><!-- End Cloudflare Web Analytics -->
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-8Q45D6XVQZ"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-8Q45D6XVQZ');
</script>
</head>
<body>
<nav>
  <a href="index.html" class="logo" style="display:inline-flex;align-items:center">A<span class="heart-i">ı</span>dollargame</a>
  <a href="index.html" class="nav-home">← HOME</a>
</nav>

<div class="hero">
  <div class="section-tag">OFFICIAL NOTE</div>
  <h1>公式note 記事一覧</h1>
  <div class="note-lead">
    <p>株式会社AIdollargameが公式noteに公開した記事{n}本です。中小企業のAI導入、実証研究の読み比べ、公的調査の読み解きを、出典をつけて書いています。自社サイトにも同じ話を書いている記事には、その行き先も並べています。</p>
    <a class="note-follow" href="https://note.com/{user}" target="_blank" rel="noopener">公式noteをフォローする →</a>
  </div>
</div>

<div class="articles-section">
  <div class="articles-grid">
<!-- AUTO-NOTE-START -->
{cards}<!-- AUTO-NOTE-END -->
  </div>

  <div class="contact-nudge">
    <img class="nudge-photo" src="aidollargame-ceo-sato-norinosuke.jpg" alt="株式会社AIdollargame 代表取締役CEO 佐藤徳之介">
    <div class="nudge-body">
      <p>記事で扱ったやり方を自社で試したい、という段階のご相談も受けています。30分の無料相談で、貴社のどの業務から始めるかまで一緒に決めます。</p>
      <a class="nudge-link" href="index.html#contact">無料で相談する →</a>
      <span style="display:inline-block;width:1.2rem"></span>
      <a class="nudge-link" href="articles/">自社サイトの記事一覧 →</a>
    </div>
  </div>
</div>

<footer>
  <div class="footer-copy">© <span id="cpy">2025</span> 株式会社AIdollargame. ALL RIGHTS RESERVED.</div>
  <div style="display:flex;gap:1.4rem;flex-wrap:wrap;">
    <a href="index.html" style="font-size:0.8rem;text-decoration:none;">ホーム</a>
    <a href="articles/" style="font-size:0.8rem;text-decoration:none;">記事一覧</a>
    <a href="company.html" style="font-size:0.8rem;text-decoration:none;">会社概要</a>
    <a href="media.html" style="font-size:0.8rem;text-decoration:none;">メディア掲載</a>
  </div>
</footer>
<script>
  (function(){{
    var y=new Date().getFullYear(), e=document.getElementById('cpy');
    if(e) e.textContent = y>2025 ? '2025-'+y : '2025';
  }})();
  /* どのnote記事が自社サイトから読まれたかをGA4で見る */
  document.addEventListener('click', function(e){{
    var a = e.target.closest ? e.target.closest('a[href*="note.com"]') : null;
    if (!a || typeof gtag !== 'function') return;
    var card = a.closest('.note-card');
    gtag('event', 'note_click', {{
      note_key: card ? card.getAttribute('data-note-key') : 'profile',
      link_text: (a.textContent || '').trim().slice(0, 50)
    }});
  }});
</script>
</body>
</html>
""".format(
        desc=escape(desc),
        site=SITE,
        css=css,
        itemlist=json.dumps(itemlist, ensure_ascii=False, indent=2),
        breadcrumb=json.dumps(breadcrumb, ensure_ascii=False, indent=2),
        cards=cards,
        n=len(items),
        user=NOTE_USER,
    ), newest


def extract_css(path):
    """記事一覧ページの<style>をそのまま借りて、見た目を一箇所で保つ。"""
    html = path.read_text(encoding="utf-8")
    m = re.search(r"<style>.*?</style>", html, re.S)
    if not m:
        raise SystemExit("articles/index.html から<style>が取れなかった")
    return m.group(0)


def patch_sitemap(newest):
    p = REPO / "sitemap.xml"
    xml = p.read_text(encoding="utf-8")
    loc = SITE + "/note.html"
    lastmod = newest.strftime("%Y-%m-%d")
    entry = (
        '  <url><loc>{}</loc><lastmod>{}</lastmod>'
        "<changefreq>weekly</changefreq><priority>0.8</priority></url>\n"
    ).format(loc, lastmod)
    if loc in xml:
        xml = re.sub(
            r"  <url><loc>" + re.escape(loc) + r"</loc>.*?</url>\n",
            entry,
            xml,
            flags=re.S,
        )
    else:
        anchor = "  <url><loc>{}/articles/</loc>".format(SITE)
        i = xml.find(anchor)
        if i == -1:
            xml = xml.replace("</urlset>", entry + "</urlset>")
        else:
            xml = xml[:i] + entry + xml[i:]
    p.write_text(xml, encoding="utf-8")


def patch_llms(items):
    p = REPO / "llms.txt"
    txt = p.read_text(encoding="utf-8")
    lines = [
        "## 公式note (Official note articles)",
        "株式会社AIdollargameが note.com で公開している記事。一覧ページ: {}/note.html".format(SITE),
        "アカウント: https://note.com/{}".format(NOTE_USER),
        "",
    ]
    for it in items:
        d = datetime.fromisoformat(it["publishAt"]).astimezone(JST).strftime("%Y-%m-%d")
        url = it.get("noteUrl") or "https://note.com/{}/n/{}".format(NOTE_USER, it["key"])
        lines.append("- {}｜{}: {}".format(d, clean_text(it["name"]), url))
    block = "<!-- NOTE-INDEX-START -->\n" + "\n".join(lines) + "\n<!-- NOTE-INDEX-END -->"
    if "<!-- NOTE-INDEX-START -->" in txt:
        txt = re.sub(
            r"<!-- NOTE-INDEX-START -->.*?<!-- NOTE-INDEX-END -->", block, txt, flags=re.S
        )
    else:
        txt = txt.rstrip() + "\n\n" + block + "\n"
    p.write_text(txt, encoding="utf-8")


def main():
    items = fetch_all()
    if not items:
        print("note記事が取得できなかったので何も書き換えない", file=sys.stderr)
        return 1
    css = extract_css(REPO / "articles" / "index.html")
    html, newest = build_html(items, css)
    (REPO / "note.html").write_text(html, encoding="utf-8")
    patch_sitemap(newest)
    patch_llms(items)
    linked = sum(1 for it in items if it["key"] in HP_COUNTERPART)
    print("note.html: {}本 (自社サイト版と相互リンク済み {}本)".format(len(items), linked))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
