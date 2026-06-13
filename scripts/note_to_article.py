#!/usr/bin/env python3
"""Convert a note markdown draft (content/note/*.md) into a site article page
under articles/<slug>.html, styled to match the site (dark theme) with full SEO
(canonical, OG, Article structured data). Re-runnable: edit the note draft and
run again to re-sync the published page.

Usage:
  python scripts/note_to_article.py <note.md> <slug> "<description>" [og-image-url]
"""
import re, sys, html
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).parent.parent
JST = timezone(timedelta(hours=9))

PAGE = """\
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<link rel="icon" type="image/svg+xml" href="../favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="../favicon-32.png">
<link rel="apple-touch-icon" sizes="180x180" href="../favicon-180.png">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | AIdollargame</title>
<meta name="description" content="{desc}">
<meta name="author" content="株式会社AIdollargame">
<meta name="theme-color" content="#0a1238">
<link rel="canonical" href="https://aidollargame.com/articles/{slug}.html">

<meta property="og:type" content="article">
<meta property="og:site_name" content="AIdollargame">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="https://aidollargame.com/articles/{slug}.html">
<meta property="og:image" content="{ogimg}">
<meta property="og:locale" content="ja_JP">
<meta property="article:published_time" content="{iso}">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{ogimg}">

<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{title}",
  "description": "{desc}",
  "datePublished": "{iso}",
  "author": {{"@type":"Organization","name":"株式会社AIdollargame"}},
  "publisher": {{"@type":"Organization","name":"AIdollargame","logo":{{"@type":"ImageObject","url":"https://aidollargame.com/og-default.png"}}}},
  "mainEntityOfPage": "https://aidollargame.com/articles/{slug}.html",
  "image": "{ogimg}",
  "inLanguage": "ja"
}}
</script>

<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Noto+Sans+JP:wght@300;400;500;700;900&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
  :root{{--cyan:#00d8ff;--blue:#1a6dff;--accent:#ff5757;--text:#eef3ff;--muted:#9aa8d0;--grad:linear-gradient(135deg,#00d8ff,#1a6dff);}}
  *{{margin:0;padding:0;box-sizing:border-box;}}
  html{{scroll-behavior:smooth;background:#0a1238;}}
  body{{background:linear-gradient(180deg,#0a1238 0%,#0c1542 50%,#0a1340 100%);color:var(--text);font-family:'Noto Sans JP',sans-serif;overflow-x:hidden;line-height:1.9;}}
  nav{{position:fixed;top:0;left:0;right:0;z-index:100;display:flex;justify-content:space-between;align-items:center;padding:1.2rem 3rem;background:rgba(6,9,26,0.88);backdrop-filter:blur(20px);border-bottom:1px solid rgba(0,245,255,0.1);}}
  .logo{{font-family:'Rajdhani',sans-serif;font-size:1.4rem;font-weight:700;color:white;text-decoration:none;}}
  .logo .ai{{color:var(--cyan);text-shadow:0 0 20px rgba(0,245,255,0.6);}}
  .nav-back{{font-family:'Share Tech Mono',monospace;font-size:0.78rem;letter-spacing:0.12em;color:var(--muted);text-decoration:none;transition:color 0.3s;}}
  .nav-back:hover{{color:var(--cyan);}}
  .hero{{padding:9rem 2rem 1.5rem;max-width:820px;margin:0 auto;}}
  .tag{{font-family:'Share Tech Mono',monospace;font-size:0.7rem;letter-spacing:0.4em;color:var(--cyan);margin-bottom:1.2rem;display:flex;align-items:center;gap:0.8rem;}}
  .tag::before{{content:'';display:inline-block;width:30px;height:1px;background:var(--cyan);}}
  h1{{font-size:clamp(1.7rem,4vw,2.6rem);font-weight:900;line-height:1.3;margin-bottom:1.2rem;}}
  .meta{{display:flex;gap:1.5rem;align-items:center;font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:var(--muted);letter-spacing:0.1em;padding-bottom:1rem;flex-wrap:wrap;}}
  .body{{max-width:820px;margin:0 auto;padding:2rem 2rem 5rem;}}
  .body h2{{font-size:1.4rem;font-weight:900;margin:3rem 0 1.1rem;padding-left:1rem;border-left:3px solid var(--cyan);line-height:1.45;}}
  .body h3{{font-size:1.1rem;font-weight:700;margin:2rem 0 0.8rem;color:#fff;}}
  .body p{{font-size:0.98rem;color:rgba(238,243,255,0.86);line-height:2.05;margin-bottom:1.3rem;}}
  .body strong{{color:#fff;font-weight:700;}}
  .body a{{color:var(--cyan);text-decoration:none;border-bottom:1px solid rgba(0,216,255,0.35);}}
  .body ul{{list-style:none;margin:0 0 1.4rem;padding:0;}}
  .body li{{position:relative;padding-left:1.4rem;margin-bottom:0.7rem;font-size:0.97rem;color:rgba(238,243,255,0.88);line-height:1.9;}}
  .body li::before{{content:'';position:absolute;left:0;top:0.7em;width:7px;height:7px;border-radius:50%;background:var(--grad);}}
  .body blockquote{{border-left:3px solid var(--accent);padding:1.1rem 1.5rem;margin:1.8rem 0;background:rgba(255,87,87,0.07);border-radius:0 6px 6px 0;font-size:1.05rem;font-weight:700;color:#fff;line-height:1.8;}}
  .body hr{{border:none;border-top:1px solid rgba(255,255,255,0.1);margin:2.5rem 0;}}
  .cta{{max-width:820px;margin:0 auto;background:linear-gradient(180deg,rgba(28,38,80,0.9),rgba(16,24,60,0.95));border:1px solid rgba(0,216,255,0.2);border-radius:10px;padding:2.4rem;text-align:center;}}
  .cta h3{{font-size:1.2rem;font-weight:900;margin-bottom:0.7rem;}}
  .cta p{{color:var(--muted);font-size:0.9rem;margin-bottom:1.6rem;}}
  .btn{{display:inline-flex;align-items:center;gap:0.6rem;padding:0.9rem 2rem;color:#001428;font-weight:700;font-size:0.9rem;border-radius:8px;background:linear-gradient(110deg,#00d8ff,#1a6dff,#00d8ff);background-size:220% 100%;text-decoration:none;}}
  footer{{border-top:1px solid rgba(255,255,255,0.08);padding:2.5rem 3rem;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;background:rgba(6,9,26,0.6);margin-top:3rem;}}
  footer .links{{display:flex;gap:1.6rem;align-items:center;flex-wrap:wrap;}}
  footer a{{font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:var(--muted);text-decoration:none;letter-spacing:0.05em;}}
  footer a:hover{{color:var(--cyan);}}
  .fc{{font-size:0.72rem;color:var(--muted);font-family:'Share Tech Mono',monospace;}}
  @media(max-width:768px){{nav{{padding:1rem 1.2rem;}}.hero,.body,.cta{{padding-left:1.2rem;padding-right:1.2rem;}}footer{{padding:2rem 1.5rem;}}}}
</style>
</head>
<body>
<nav>
  <a href="../index.html" class="logo" style="display:inline-flex;align-items:center"><span class="ai">AI</span>dollargame</a>
  <a href="./index.html" class="nav-back">← 記事一覧</a>
</nav>
<div class="hero">
  <div class="tag">{cat}</div>
  <h1>{title}</h1>
  <div class="meta"><span>{date}</span><span>株式会社AIdollargame</span></div>
</div>
<article class="body">
{body}
<div class="cta">
  <h3>AIで“めんどくさい”を減らして、楽しい時間を。</h3>
  <p>AIプロダクト開発・AI導入支援の株式会社AIdollargame。まずは無料のAI活用度診断から。</p>
  <a href="../shindan.html" class="btn">AI活用度診断を試す →</a>
</div>
</article>
<footer>
  <a href="../index.html" class="logo"><span class="ai">AI</span>dollargame</a>
  <div class="links">
    <a href="https://note.com/aidollargame" target="_blank" rel="me noopener">note ↗</a>
    <a href="../privacy.html">プライバシーポリシー</a>
    <a href="../tokushoho.html">特定商取引法に基づく表記</a>
  </div>
  <div class="fc">© 2026 株式会社AIdollargame. ALL RIGHTS RESERVED.</div>
</footer>
</body>
</html>
"""


def inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(https?://[^\s　)）]+)", r'<a href="\1" target="_blank" rel="noopener">\1</a>', text)
    return text


def md_to_body(md):
    # drop leading HTML comment + first H1 (used as title), and trailing note-only meta
    lines = md.splitlines()
    lines = [l for l in lines if not l.strip().startswith("<!--")]
    out, i, in_ul = [], 0, False
    # skip until after first H1
    while i < len(lines) and not lines[i].startswith("# "):
        i += 1
    i += 1  # skip the H1 line itself

    def close_ul():
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    for line in lines[i:]:
        s = line.strip()
        if s.startswith("**ハッシュタグ") or s.startswith("**サムネ"):
            break  # note-only meta — stop
        if not s:
            close_ul(); continue
        if s == "---":
            close_ul(); out.append("<hr>"); continue
        if s.startswith("## "):
            close_ul(); out.append(f"<h2>{inline(s[3:])}</h2>"); continue
        if s.startswith("### "):
            close_ul(); out.append(f"<h3>{inline(s[4:])}</h3>"); continue
        if s.startswith("> "):
            close_ul(); out.append(f"<blockquote>{inline(s[2:])}</blockquote>"); continue
        if s.startswith("- "):
            if not in_ul:
                out.append("<ul>"); in_ul = True
            out.append(f"<li>{inline(s[2:])}</li>"); continue
        close_ul(); out.append(f"<p>{inline(s)}</p>")
    close_ul()
    return "\n".join(out)


def main():
    src, slug, desc = sys.argv[1], sys.argv[2], sys.argv[3]
    ogimg = sys.argv[4] if len(sys.argv) > 4 else f"https://aidollargame.com/og-articles-{slug}.png"
    cat = sys.argv[5] if len(sys.argv) > 5 else "INSIGHT"
    md = Path(src).read_text(encoding="utf-8")
    m = re.search(r"^# (.+)$", md, re.M)
    title = m.group(1).strip()
    now = datetime.now(JST)
    page = PAGE.format(title=html.escape(title), desc=html.escape(desc), slug=slug,
                       ogimg=ogimg, iso=now.strftime("%Y-%m-%d"),
                       date=now.strftime("%Y / %m / %d"), cat=cat,
                       body=md_to_body(md))
    out = ROOT / "articles" / f"{slug}.html"
    out.write_text(page, encoding="utf-8")
    print(f"Wrote {out}  (title: {title})")


if __name__ == "__main__":
    main()
