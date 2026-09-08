#!/usr/bin/env python3
"""articles/ の記事が、検索とAIに拾われる3つの入口すべてに載っているかを点検する。

なぜ必要か:
  記事を1本足すたびに sitemap.xml / llms.txt / articles/index.html の3箇所を
  手で書き足す運用になっていた。実際に漏れが出ている(2026-09-08時点で
  sitemapに1本、llms.txtに9本、記事一覧ページに4本の欠落)。
  記事本数を増やすほど漏れる構造なので、機械で毎回突き合わせる。

  ファイルは触らない。何が抜けているかを出すだけ。直すのは人間(またはClaude)。

使い方:
  python3 scripts/check_site_index.py        欠落があれば一覧を出して終了コード1
  python3 scripts/check_site_index.py --quiet 欠落が無ければ何も出さない
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
ARTICLES = REPO / "articles"

# 記事一覧ページ(articles/index.html)にはあえて載せないもの。
# 載せない理由を必ず書く。理由が説明できないものはここに入れない。
INDEX_SKIP = {
    "nbc-2026-07.html": "メディア出演の告知。media.html とトップに掲載しているため記事グリッドには出さない",
    "nbc-kigyojuku-2026-07.html": "登壇レポート。media.html とトップに掲載しているため記事グリッドには出さない",
}


def article_files():
    return sorted(
        p.name for p in ARTICLES.glob("*.html") if p.name != "index.html"
    )


def read(rel):
    return (REPO / rel).read_text(encoding="utf-8")


def title_of(name):
    html = (ARTICLES / name).read_text(encoding="utf-8")
    m = re.search(r"<title>([^<]*)</title>", html)
    t = m.group(1) if m else name
    return t.split("|")[0].strip()


def published_of(name):
    html = (ARTICLES / name).read_text(encoding="utf-8")
    m = re.search(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})', html)
    return m.group(1) if m else ""


def main():
    quiet = "--quiet" in sys.argv
    files = article_files()
    sitemap = read("sitemap.xml")
    llms = read("llms.txt")
    index = read("articles/index.html")

    missing = {"sitemap.xml": [], "llms.txt": [], "articles/index.html": []}
    for name in files:
        if "articles/" + name not in sitemap:
            missing["sitemap.xml"].append(name)
        if "articles/" + name not in llms:
            missing["llms.txt"].append(name)
        if './%s"' % name not in index and name not in INDEX_SKIP:
            missing["articles/index.html"].append(name)

    # sitemapに書いてあるのに実体が無いURL(公開後に404になる)
    dead = [
        u
        for u in sorted(set(re.findall(r"articles/([a-z0-9.-]+\.html)", sitemap)))
        if not (ARTICLES / u).exists()
    ]

    total = sum(len(v) for v in missing.values()) + len(dead)
    if total == 0:
        if not quiet:
            print("記事 %d本: sitemap.xml / llms.txt / 記事一覧ページ すべてに掲載済み" % len(files))
            if INDEX_SKIP:
                print("(記事一覧ページから意図的に除外: %d本)" % len(INDEX_SKIP))
        return 0

    print("記事 %d本を点検して %d件の欠落があった" % (len(files), total))
    for where, names in missing.items():
        if not names:
            continue
        print("\n[%s に無い記事 %d本]" % (where, len(names)))
        for n in names:
            print("  %s  %s  %s" % (published_of(n) or "日付不明", n, title_of(n)))
    if dead:
        print("\n[sitemapにあるが実ファイルが無い %d件]" % len(dead))
        for n in dead:
            print("  " + n)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
