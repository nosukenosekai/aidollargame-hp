#!/usr/bin/env python3
"""content/note/<日付>.md をHPの記事ページ(articles/<slug>.html)に変換し、
トップの記事・コラム / 記事一覧 / sitemap.xml / llms.txt に登録する。

使い方: python3 scripts/note_to_article.py 2026-11-02:ai-shiken-sennen-tani-2026 [日付:slug ...]
slug は英小文字・数字・ハイフンで、内容が分かるローマ字にする。既にある slug は止まる。
"""
import re, html, json, shutil, sys
from pathlib import Path

R = Path(__file__).resolve().parent.parent
A = R / 'articles'
TPL = (A / 'ai-koka-hakarikata-2026.html').read_text()

NOTES = [tuple(x.split(':', 1)) for x in sys.argv[1:]]
PREV = []

CAT = {'RESEARCH': ('insight', '研究'), 'NEWS': ('news', 'ニュース'), 'COLUMN': ('insight', '代表の判断メモ')}


def esc(s):
    return html.escape(s, quote=True)


def inline(s):
    s = esc(s)
    return re.sub(r'(https?://[^\s）)<」]+)', lambda m: f'<a href="{m.group(1)}" target="_blank" rel="noopener">{m.group(1)}</a>', s)


def category(theme):
    if '研究' in theme and '相談' not in theme:
        return 'RESEARCH'
    if 'ニュース' in theme:
        return 'NEWS'
    return 'COLUMN'


def parse(date, slug):
    t = (R / 'content/note' / f'{date}.md').read_text()
    theme = (re.search(r'<!--(.*?)-->', t, re.S) or [None, ''])[1]
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    t = t.split('## 私たちについて')[0]
    lines = t.strip('\n').splitlines()
    title = next(l[2:].strip() for l in lines if l.startswith('# '))
    alt = next((re.match(r'!\[(.*?)\]', l).group(1) for l in lines if l.startswith('![')), title)
    body, lst, out_src = [], None, False
    for l in lines:
        if l.startswith('# ') or l.startswith('!['):
            continue
        s = l.rstrip()
        m_ol = re.match(r'^(\d+)\. (.*)', s)
        is_ul = s.startswith('- ')
        if lst and not ((lst == 'ol' and m_ol) or (lst == 'ul' and is_ul)):
            body.append(f'</{lst}>'); lst = None
        if s.strip() in ('---', ''):
            continue
        if s.startswith('### '):
            body.append(f'<h3>{inline(s[4:])}</h3>')
        elif s.startswith('## '):
            out_src = s[3:].strip() in ('出典', '出典・参考', '参考')
            body.append(f'<h2>{inline(s[3:])}</h2>')
        elif m_ol:
            if not lst: body.append('<ol>'); lst = 'ol'
            body.append(f'<li>{inline(m_ol.group(2))}</li>')
        elif is_ul and not out_src:
            if not lst: body.append('<ul>'); lst = 'ul'
            body.append(f'<li>{inline(s[2:])}</li>')
        elif out_src or re.fullmatch(r'https?://\S+', s.strip()) or s.startswith('写真'):
            body.append(f'<p class="src">{inline(s[2:] if is_ul else s)}</p>')
        else:
            body.append(f'<p>{inline(s)}</p>')
    if lst: body.append(f'</{lst}>')
    paras = [re.sub(r'<[^>]+>', '', b) for b in body if b.startswith('<p>')]
    lead = paras[0] if paras else title
    sents = re.findall(r'[^。]+。', lead) or [lead]
    desc = ''
    for s in sents:
        if len(desc + s) > 120: break
        desc += s
    desc = desc or sents[0][:120]
    head, _, rest = title.partition('。')
    short = head if rest else title
    card_desc = rest.strip() if rest.strip() else sents[0][:70]
    plain = re.sub(r'<[^>]+>', '', ''.join(body))
    return dict(date=date, slug=slug, title=title, short=short, alt=alt, cat=category(theme),
                desc=desc, card_desc=card_desc, body='\n'.join(body),
                mins=max(3, round(len(plain) / 500)))


def build(a, related):
    t = TPL
    i0 = t.index('<script type="application/ld+json">')
    head_top = t[:i0]
    head_top = re.sub(r'<title>.*?</title>', f'<title>{esc(a["title"])} | AIdollargame</title>', head_top)
    head_top = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{esc(a["desc"])}">', head_top)
    head_top = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="https://aidollargame.com/articles/{a["slug"]}.html">', head_top)
    url = f'https://aidollargame.com/articles/{a["slug"]}.html'
    img = f'https://aidollargame.com/articles/{a["slug"]}-hero.jpg'
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "ホーム", "item": "https://aidollargame.com/"},
        {"@type": "ListItem", "position": 2, "name": "記事一覧", "item": "https://aidollargame.com/articles/"},
        {"@type": "ListItem", "position": 3, "name": a['short'], "item": url}]}
    art = {"@context": "https://schema.org", "@type": "Article", "headline": a['short'], "description": a['desc'],
           "datePublished": a['date'], "author": {"@type": "Organization", "name": "AIdollargame 編集部"},
           "publisher": {"@type": "Organization", "name": "AIdollargame", "logo": {"@type": "ImageObject", "url": "https://aidollargame.com/og-default.png"}},
           "mainEntityOfPage": url, "image": img, "inLanguage": "ja"}
    j = lambda o: json.dumps(o, ensure_ascii=False, indent=2).replace('</', '<\\/')
    meta = f'''<script type="application/ld+json">
{j(crumbs)}
</script>

<meta property="og:type" content="article">
<meta property="og:site_name" content="株式会社AIdollargame">
<meta property="og:title" content="{esc(a['short'])}">
<meta property="og:description" content="{esc(a['desc'])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{img}">
<meta property="og:locale" content="ja_JP">
<meta property="article:published_time" content="{a['date']}">
<meta property="article:author" content="AIdollargame 編集部">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(a['short'])}">
<meta name="twitter:description" content="{esc(a['desc'])}">
<meta name="twitter:image" content="{img}">

<script type="application/ld+json">
{j(art)}
</script>
'''
    i1 = t.index('\n<style>')
    i2 = t.index('<div class="hero">')
    style_to_nav = t[i1:i2]
    d = a['date'].replace('-', ' / ')
    hero = f'''<div class="hero">
  <div class="tag">{a['cat']}</div>
  <h1>{esc(a['title'])}</h1>
  <div class="meta"><span>{d}</span><span>AIdollargame 編集部</span><span>読了 約{a['mins']}分</span></div>
</div>
<article class="body">

<figure style="margin:0 0 2.6rem;">
  <img src="{a['slug']}-hero.jpg" alt="{esc(a['alt'])}" style="width:100%;height:auto;border-radius:14px;display:block;">
</figure>

{a['body']}
'''
    i3 = t.index('\n<p class="src">この記事と同じ内容を')
    tail = t[i3:]
    rel = '\n'.join(f'    <a href="./{r["slug"]}.html" class="rcard"><div class="rt">{r["cat"]}</div><div class="rttl">{esc(r["short"])}</div></a>' for r in related)
    tail = re.sub(r'(<div class="rgrid">\n).*?(\n  </div>\n</div>)', lambda m: m.group(1) + rel + m.group(2), tail, count=1, flags=re.S)
    return head_top + meta + style_to_nav + hero + tail


def main():
    arts = [parse(d, s) for d, s in NOTES]
    for a in arts:
        assert not (A / f'{a["slug"]}.html').exists(), a['slug']
    newest = sorted(arts, key=lambda a: a['date'], reverse=True)
    for a in arts:
        rel = [r for r in newest if r is not a][:5]
        (A / f'{a["slug"]}.html').write_text(build(a, rel))
        shutil.copyfile(R / 'content/note/img' / f'{a["date"]}.jpg', A / f'{a["slug"]}-hero.jpg')

    # 10/5の5本の情報を記事ページから拾う
    prev = []
    for s in PREV:
        h = (A / f'{s}.html').read_text()
        prev.append(dict(slug=s, date=re.search(r'"datePublished": "([^"]+)"', h).group(1),
                         title=html.unescape(re.search(r'<h1>(.*?)</h1>', h).group(1)),
                         short=html.unescape(re.search(r'<meta property="og:title" content="([^"]*)"', h).group(1)),
                         card_desc=html.unescape(re.search(r'<meta property="og:description" content="([^"]*)"', h).group(1)),
                         cat=re.search(r'<div class="tag">(\w+)</div>', h).group(1)))
    allnew = sorted(arts + prev, key=lambda a: a['date'], reverse=True)

    # 記事一覧
    idx = A / 'index.html'
    s = idx.read_text()
    cards = []
    for a in allnew:
        tag, label = CAT.get(a['cat'], ('insight', '研究'))
        cards.append(f'''    <a href="./{a['slug']}.html" class="article-card" data-tag="{tag}">
      <div class="card-color-bar"></div>
      <div class="card-image" style="background-image:url('./{a['slug']}-hero.jpg')"></div>
      <div class="card-body">
        <div class="card-tag">{label}</div>
        <div class="card-date">{a['date'].replace('-', ' / ')}</div>
        <div class="card-title">{esc(a['title'])}</div>
        <div class="card-desc">{esc(a.get('desc', a['card_desc']))}</div>
        <div class="card-link">READ MORE →</div>
      </div>
    </a>''')
    mk = '<!-- AUTO-ARTICLES-START -->\n'
    s = s.replace(mk, mk + '\n'.join(cards) + '\n', 1)
    idx.write_text(s)

    # トップの記事・コラム: 先頭5枚を最新5本に差し替え
    top = R / 'index.html'
    s = top.read_text()
    start = s.index('<div class="posts">', s.index('data-edit="column-lead"'))
    seg_end = s.index('</div>\n  </div>', start)
    seg = s[start:seg_end]
    posts = re.findall(r'      <a class="post" href="\./articles/.*?\n      </a>\n', seg, re.S)
    first5 = posts[:5]
    cur = []
    for p in first5:
        g = lambda pat: html.unescape(re.search(pat, p).group(1))
        cur.append(dict(slug=g(r'articles/([^"]+)\.html'), cat=g(r'class="cat">([^<]*)<'),
                        date=g(r'class="date">([^<]*)<').replace(' / ', '-'),
                        short=g(r'class="ptitle">([^<]*)<'), card_desc=g(r'class="pdesc">([^<]*)<')))
    top5 = sorted(allnew + [c for c in cur if c['slug'] not in {a['slug'] for a in allnew}],
                  key=lambda a: a['date'], reverse=True)[:5]
    new5 = []
    for k, a in enumerate(top5):
        new5.append(f'''      <a class="post" href="./articles/{a['slug']}.html" data-rv="up" style="--d:{k*120}ms">
        <div class="thumb-wrap"><div class="thumb" style="background-image:url('./articles/{a['slug']}-hero.jpg')"></div></div>
        <div class="pbody">
          <div class="meta-row"><span class="cat">{a['cat']}</span><span class="date">{a['date'].replace('-', ' / ')}</span></div>
          <div class="ptitle">{esc(a['short'])}</div>
          <div class="pdesc">{esc(a['card_desc'])}</div>
        </div>
      </a>
''')
    newseg = seg.replace(''.join(first5), ''.join(new5), 1)
    assert newseg != seg
    s = s[:start] + newseg + s[seg_end:]
    top.write_text(s)

    # sitemap
    sm = R / 'sitemap.xml'
    s = sm.read_text()
    add = ''.join(f'  <url><loc>https://aidollargame.com/articles/{a["slug"]}.html</loc><lastmod>{a["date"]}</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>\n'
                  for a in allnew if f'/articles/{a["slug"]}.html' not in s)
    s = s.replace('</urlset>', add + '</urlset>')
    sm.write_text(s)

    # llms.txt
    ll = R / 'llms.txt'
    s = ll.read_text()
    anchor = next(l for l in s.splitlines() if 'yoyaku-daiko-16ji-2026.html' in l)
    add = '\n'.join(f'- {a["title"]}: https://aidollargame.com/articles/{a["slug"]}.html' for a in reversed(allnew) if a['slug'] not in s)
    s = s.replace(anchor, anchor + '\n' + add, 1)
    ll.write_text(s)
    for a in arts:
        print(f'https://aidollargame.com/articles/{a["slug"]}.html  {a["title"]}')


if not NOTES:
    sys.exit(__doc__)
main()
