#!/usr/bin/env python3
"""Sitemap generator for AIdollargame HP.

Scans every published HTML page and emits sitemap.xml with Google image-sitemap
entries (og:image + inline <img>) so that all first-party brand images get
discovered and associated with the aidollargame.com domain. Run this after
generate_articles.py (or any time pages/images change)."""

import re, json, html
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
ARTICLES_DIR = REPO_ROOT / "articles"
ARTICLES_INDEX_JSON = ARTICLES_DIR / "_articles_index.json"
SITEMAP = REPO_ROOT / "sitemap.xml"
BASE = "https://aidollargame.com/"
JST = timezone(timedelta(hours=9))

# Pages we don't want in the sitemap (search-console verification, legal-only).
EXCLUDE = {"google4e4d1184d07ded76.html"}

OG_RE = re.compile(r'<meta\s+property="og:image"\s+content="([^"]+)"', re.I)
IMG_RE = re.compile(r'<img[^>]+src="([^"]+)"', re.I)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S | re.I)


def to_abs(url, page_url):
    """Resolve an image URL to an absolute https://aidollargame.com/... URL."""
    if url.startswith("http"):
        return url
    if url.startswith("/"):
        return BASE.rstrip("/") + url
    # relative to the page's directory
    base_dir = page_url.rsplit("/", 1)[0] + "/"
    while url.startswith("../"):
        url = url[3:]
        base_dir = base_dir.rstrip("/").rsplit("/", 1)[0] + "/"
    return base_dir + url


def page_loc(path: Path) -> str:
    rel = path.relative_to(REPO_ROOT).as_posix()
    if rel == "index.html":
        return BASE
    if rel == "articles/index.html":
        return BASE + "articles/"
    return BASE + rel


def collect_images(text, page_url):
    """Return ordered-unique absolute image URLs referenced by a page."""
    urls = []
    for m in OG_RE.finditer(text):
        urls.append(to_abs(m.group(1), page_url))
    for m in IMG_RE.finditer(text):
        src = m.group(1)
        if src.startswith("data:") or src.endswith(".svg"):
            continue
        urls.append(to_abs(src, page_url))
    seen, out = set(), []
    for u in urls:
        # Image sitemaps should only list first-party images we own; skip
        # third-party assets (e.g. external tool favicons) and duplicates.
        if not u.startswith(BASE):
            continue
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def article_dates():
    """slug -> YYYY-MM-DD from the articles index ledger."""
    dates = {}
    if ARTICLES_INDEX_JSON.exists():
        for a in json.loads(ARTICLES_INDEX_JSON.read_text(encoding="utf-8")):
            d = (a.get("date") or "").replace(" ", "").replace("/", "-")
            if re.match(r"\d{4}-\d{2}-\d{2}", d):
                dates[a["slug"]] = d
    return dates


def priority_for(rel):
    if rel == "index.html":
        return "1.0", "weekly"
    if rel == "articles/index.html":
        return "0.8", "weekly"
    if rel in {"aiside.html", "human-clone-ai.html", "line-ai-agent.html",
               "ai-consulting.html", "shindan.html"}:
        return "0.9", "monthly"
    if rel == "ai-yougo.html":
        return "0.8", "monthly"
    if rel.startswith("articles/"):
        return "0.7", "monthly"
    return "0.5", "monthly"


def build():
    dates = article_dates()
    pages = [REPO_ROOT / "index.html"]
    pages += sorted(p for p in REPO_ROOT.glob("*.html")
                    if p.name not in EXCLUDE and p.name != "index.html")
    pages += [ARTICLES_DIR / "index.html"]
    pages += sorted(p for p in ARTICLES_DIR.glob("*.html") if p.name != "index.html")

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
             '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']

    for path in pages:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(REPO_ROOT).as_posix()
        loc = page_loc(path)
        prio, freq = priority_for(rel)
        tm = TITLE_RE.search(text)
        title = re.sub(r"\s+", " ", tm.group(1)).strip() if tm else "AIdollargame"
        title = html.escape(title)

        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        slug = path.stem
        if rel.startswith("articles/") and slug in dates:
            lines.append(f"    <lastmod>{dates[slug]}</lastmod>")
        lines.append(f"    <changefreq>{freq}</changefreq>")
        lines.append(f"    <priority>{prio}</priority>")
        for img in collect_images(text, loc):
            lines.append("    <image:image>")
            lines.append(f"      <image:loc>{html.escape(img)}</image:loc>")
            lines.append(f"      <image:title>{title}</image:title>")
            lines.append("    </image:image>")
        lines.append("  </url>")

    lines.append("</urlset>")
    SITEMAP.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {SITEMAP} ({len(pages)} pages)")


if __name__ == "__main__":
    build()
