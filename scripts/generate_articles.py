#!/usr/bin/env python3
"""Weekly AI news article generator for AIdollargame HP"""

import os, re, json, feedparser, anthropic
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
ARTICLES_DIR = REPO_ROOT / "articles"
MAIN_INDEX = REPO_ROOT / "index.html"
ARTICLES_INDEX = ARTICLES_DIR / "index.html"
JST = timezone(timedelta(hours=9))

ARTICLE_HTML = """\
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<link rel="icon" type="image/svg+xml" href="../favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="../favicon-32.png">
<link rel="apple-touch-icon" sizes="180x180" href="../favicon-180.png">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | AIdollargame</title>
<meta name="description" content="{description}">
<meta name="author" content="AIdollargame 編集部">
<meta name="theme-color" content="#0a1238">
<link rel="canonical" href="https://aidollargame.com/articles/{slug}.html">

<meta property="og:type" content="article">
<meta property="og:site_name" content="AIdollargame">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="https://aidollargame.com/articles/{slug}.html">
<meta property="og:image" content="https://aidollargame.com/og-default.png">
<meta property="og:locale" content="ja_JP">
<meta property="article:published_time" content="{date_iso}">
<meta property="article:author" content="AIdollargame 編集部">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="https://aidollargame.com/og-default.png">

<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{title}",
  "description": "{description}",
  "datePublished": "{date_iso}",
  "author": {{"@type":"Organization","name":"AIdollargame 編集部"}},
  "publisher": {{
    "@type":"Organization",
    "name":"AIdollargame",
    "logo":{{"@type":"ImageObject","url":"https://aidollargame.com/og-default.png"}}
  }},
  "mainEntityOfPage": "https://aidollargame.com/articles/{slug}.html",
  "image": "https://aidollargame.com/og-default.png",
  "inLanguage": "ja"
}}
</script>

<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Noto+Sans+JP:wght@300;400;500;700;900&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
  :root{{--cyan:#00d8ff;--blue:#1a6dff;--accent:#ff5757;--dark:#0a1238;--text:#eef3ff;--muted:#9aa8d0;--grad:linear-gradient(135deg,#00d8ff,#1a6dff);}}
  *{{margin:0;padding:0;box-sizing:border-box;}}
  html{{scroll-behavior:smooth;background:#0a1238;}}
  body{{background:linear-gradient(180deg,#0a1238 0%,#0c1542 50%,#0a1340 100%);color:var(--text);font-family:'Noto Sans JP',sans-serif;overflow-x:hidden;line-height:1.8;}}
  nav{{position:fixed;top:0;left:0;right:0;z-index:100;display:flex;justify-content:space-between;align-items:center;padding:1.2rem 3rem;background:rgba(6,9,26,0.88);backdrop-filter:blur(20px);border-bottom:1px solid rgba(0,245,255,0.1);}}
  .logo{{font-family:'Rajdhani',sans-serif;font-size:1.4rem;font-weight:700;color:white;text-decoration:none;}}
  .logo .ai{{color:var(--cyan);text-shadow:0 0 20px rgba(0,245,255,0.6);}}
  .nav-back{{font-family:'Share Tech Mono',monospace;font-size:0.78rem;letter-spacing:0.12em;color:var(--muted);text-decoration:none;transition:color 0.3s;}}
  .nav-back:hover{{color:var(--cyan);}}
  .hero{{padding:9rem 2rem 4rem;max-width:800px;margin:0 auto;}}
  .tag{{font-family:'Share Tech Mono',monospace;font-size:0.7rem;letter-spacing:0.4em;color:var(--cyan);margin-bottom:1.2rem;display:flex;align-items:center;gap:0.8rem;}}
  .tag::before{{content:'';display:inline-block;width:30px;height:1px;background:var(--cyan);}}
  h1{{font-size:clamp(1.8rem,4vw,2.8rem);font-weight:900;line-height:1.25;margin-bottom:1.5rem;}}
  .meta{{display:flex;gap:2rem;align-items:center;font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:var(--muted);letter-spacing:0.1em;padding-bottom:2rem;border-bottom:1px solid rgba(255,255,255,0.08);flex-wrap:wrap;}}
  .body{{max-width:800px;margin:0 auto;padding:3rem 2rem 6rem;}}
  .body h2{{font-size:1.4rem;font-weight:900;margin:3.5rem 0 1.2rem;padding-left:1rem;border-left:3px solid var(--cyan);line-height:1.4;}}
  .body p{{font-size:0.97rem;color:rgba(238,243,255,0.85);line-height:2.1;margin-bottom:1.4rem;}}
  .body strong{{color:#fff;font-weight:700;}}
  .body blockquote{{border-left:3px solid var(--accent);padding:1.2rem 1.5rem;margin:2rem 0;background:rgba(255,87,87,0.06);border-radius:0 6px 6px 0;}}
  .body blockquote p{{margin-bottom:0;font-style:italic;color:var(--text);font-size:1.05rem;}}
  .cta{{background:linear-gradient(180deg,rgba(28,38,80,0.9),rgba(16,24,60,0.95));border:1px solid rgba(0,216,255,0.2);border-radius:10px;padding:3rem;margin:4rem 0 0;text-align:center;}}
  .cta h3{{font-size:1.3rem;font-weight:900;margin-bottom:0.8rem;}}
  .cta p{{color:var(--muted);font-size:0.9rem;margin-bottom:2rem;}}
  .btn{{display:inline-flex;align-items:center;gap:0.6rem;padding:0.9rem 2rem;color:#001428;font-weight:700;font-size:0.9rem;border-radius:8px;background:linear-gradient(110deg,#00d8ff 0%,#1a6dff 50%,#00d8ff 100%);background-size:220% 100%;text-decoration:none;transition:transform 0.25s,box-shadow 0.4s;}}
  .btn:hover{{transform:translateY(-2px);box-shadow:0 14px 36px -8px rgba(0,216,255,0.6);}}
  .related{{max-width:800px;margin:0 auto;padding:0 2rem 6rem;}}
  .related h3{{font-family:'Share Tech Mono',monospace;font-size:0.72rem;letter-spacing:0.3em;color:var(--muted);margin-bottom:1.5rem;}}
  .rgrid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:1rem;}}
  .rcard{{background:linear-gradient(180deg,rgba(28,38,80,0.9),rgba(16,24,60,0.95));border:1px solid rgba(255,255,255,0.08);border-radius:8px;padding:1.4rem;text-decoration:none;color:inherit;transition:all 0.3s;display:block;}}
  .rcard:hover{{border-color:rgba(0,216,255,0.35);transform:translateY(-4px);}}
  .rcard .rt{{font-family:'Share Tech Mono',monospace;font-size:0.65rem;color:var(--cyan);margin-bottom:0.5rem;}}
  .rcard .rttl{{font-size:0.88rem;font-weight:700;line-height:1.5;}}
  footer{{border-top:1px solid rgba(255,255,255,0.08);padding:2.5rem 3rem;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;background:rgba(6,9,26,0.6);}}
  .fc{{font-size:0.75rem;color:var(--muted);font-family:'Share Tech Mono',monospace;}}
  @media(max-width:768px){{nav{{padding:1rem 1.2rem;}}.hero,.body,.related{{padding-left:1.2rem;padding-right:1.2rem;}}footer{{padding:2rem 1.5rem;}}}}
</style>
</head>
<body>
<nav>
  <a href="../index.html" class="logo" style="display:inline-flex;align-items:center"><span class="ai">AI</span>dollargame</a>
  <a href="./index.html" class="nav-back">← ARTICLES</a>
</nav>
<div class="hero">
  <div class="tag">NEWS</div>
  <h1>{title}</h1>
  <div class="meta"><span>{date}</span><span>AIdollargame 編集部</span><span>読了 約3分</span></div>
</div>
<article class="body">
{body}
<div class="cta">
  <h3>AIの最新動向をビジネスに活かしたい方へ</h3>
  <p>プロダクトの相談でも、AI導入の相談でも。まずは話しかけてください。</p>
  <a href="../index.html#contact" class="btn">話しかける →</a>
</div>
</article>
<div class="related">
  <h3>RELATED ARTICLES</h3>
  <div class="rgrid">
    <a href="./ai-adoption-now.html" class="rcard"><div class="rt">INSIGHT</div><div class="rttl">2026年、AIを入れない会社が直面するリスク</div></a>
    <a href="./ai-frees-humans.html" class="rcard"><div class="rt">PHILOSOPHY</div><div class="rttl">「作業はAIに、愛は人間に」の本当の意味</div></a>
    <a href="./ai-and-future.html" class="rcard"><div class="rt">FUTURE</div><div class="rttl">AIが役割を引き受けるとき、人間は何を手に入れるか</div></a>
  </div>
</div>
<footer>
  <a href="../index.html" class="logo"><span class="ai">AI</span>dollargame</a>
  <div class="fc">© 2025 株式会社AIdollargame. ALL RIGHTS RESERVED.</div>
</footer>
</body>
</html>"""


def fetch_news():
    feeds = [
        "https://news.google.com/rss/search?q=AI+LLM+large+language+model&hl=en&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=OpenAI+Anthropic+Google+AI+2026&hl=en&gl=US&ceid=US:en",
    ]
    items, seen = [], set()
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:15]:
                t = e.title
                if t not in seen:
                    seen.add(t)
                    items.append({"title": t, "summary": getattr(e, "summary", "")[:300]})
        except Exception as ex:
            print(f"Feed error: {ex}")
    return items[:25]


def generate_articles(news_items, date_str):
    client = anthropic.Anthropic()
    news_text = "\n".join(
        f"{i+1}. {x['title']}\n   {x['summary'][:200]}"
        for i, x in enumerate(news_items)
    )
    prompt = f"""あなたはAIdollargame（AI企業）のコンテンツライターです。
今日: {date_str}
ビジョン: 「作業はAIに、愛は人間に」— AIが役割仕事を担い、人間が人間らしい時間を取り戻す

以下のAI最新ニュースから最も重要な3つを選んで、日本語記事を生成してください。

ニュース:
{news_text}

次のJSON形式のみで返答してください（マークダウン・コードブロック不要）:
{{"articles":[{{"slug":"英数字ハイフンのみのファイル名例:gpt5-announced","title":"日本語タイトル30字以内","description":"カード説明60字以内","body":"<p>...</p>\\n<h2>...</h2>\\n<p>...</p>\\n<blockquote><p>...</p></blockquote>"}}]}}

本文要件: 600-800字, h2を2-3個, blockquote1個, AIdollargameのビジョンと絡める, <strong>で重要語強調"""

    msg = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=6000,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)["articles"]


def make_card_articles_index(article, date_str):
    return (
        f'    <a href="./{article["slug"]}.html" class="article-card" data-tag="news">\n'
        f'      <div class="card-color-bar accent"></div>\n'
        f'      <div class="card-body">\n'
        f'        <div class="card-tag accent">NEWS</div>\n'
        f'        <div class="card-date">{date_str}</div>\n'
        f'        <div class="card-title">{article["title"]}</div>\n'
        f'        <div class="card-desc">{article["description"]}</div>\n'
        f'        <div class="card-link">READ MORE →</div>\n'
        f'      </div>\n'
        f'    </a>'
    )


def make_card_main_index(article, date_str):
    return (
        f'    <a href="./articles/{article["slug"]}.html" class="article-card">\n'
        f'      <div class="article-body-inner">\n'
        f'        <div class="article-cat">NEWS</div>\n'
        f'        <div class="article-date">{date_str}</div>\n'
        f'        <div class="article-title-card">{article["title"]}</div>\n'
        f'        <div class="article-desc">{article["description"]}</div>\n'
        f'        <div class="article-link">READ MORE →</div>\n'
        f'      </div>\n'
        f'    </a>'
    )


def update_articles_index(articles, date_str):
    content = ARTICLES_INDEX.read_text(encoding="utf-8")
    new_cards = "\n".join(make_card_articles_index(a, date_str) for a in articles)
    content = content.replace(
        "<!-- AUTO-ARTICLES-START -->",
        f"<!-- AUTO-ARTICLES-START -->\n{new_cards}\n",
    )
    ARTICLES_INDEX.write_text(content, encoding="utf-8")


def update_main_index(articles, date_str):
    content = MAIN_INDEX.read_text(encoding="utf-8")
    new_cards = "\n".join(make_card_main_index(a, date_str) for a in articles)

    m = re.search(
        r"<!-- ARTICLES-GRID-START -->(.*?)<!-- ARTICLES-GRID-END -->",
        content,
        re.DOTALL,
    )
    if not m:
        print("ARTICLES-GRID markers not found in index.html, skipping")
        return

    old_cards = re.findall(r'<a href="./articles/.*?</a>', m.group(1), re.DOTALL)
    kept_html = "\n".join(old_cards[:3])

    replacement = (
        f"<!-- ARTICLES-GRID-START -->\n{new_cards}\n{kept_html}\n"
        f"    <!-- ARTICLES-GRID-END -->"
    )
    content = re.sub(
        r"<!-- ARTICLES-GRID-START -->.*?<!-- ARTICLES-GRID-END -->",
        replacement,
        content,
        flags=re.DOTALL,
    )
    MAIN_INDEX.write_text(content, encoding="utf-8")


def main():
    print("Fetching news...")
    news = fetch_news()
    if not news:
        print("No news fetched, exiting")
        return
    print(f"Got {len(news)} items. Generating articles with Claude...")

    today = datetime.now(JST)
    date_str = today.strftime("%Y / %m / %d")
    date_iso = today.strftime("%Y-%m-%d")

    articles = generate_articles(news, date_str)

    for a in articles:
        html = ARTICLE_HTML.format(
            title=a["title"],
            description=a["description"],
            slug=a["slug"],
            date=date_str,
            date_iso=date_iso,
            body=a["body"],
        )
        path = ARTICLES_DIR / f"{a['slug']}.html"
        path.write_text(html, encoding="utf-8")
        print(f"Saved: {path.name}")

    update_articles_index(articles, date_str)
    update_main_index(articles, date_str)
    print("Done.")


if __name__ == "__main__":
    main()
