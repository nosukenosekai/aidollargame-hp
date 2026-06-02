---
name: new-article
description: AIdollargame(aidollargame.com)のサイトに新しいニュース/コラム記事を1本追加するときに使う。記事HTMLの作成、記事一覧(articles/index.html)とトップ(index.html)へのカード追加、sitemap.xmlへの登録、OG画像の用意までを一貫して行う。「記事追加して」「〇〇のテーマで記事書いて」と言われたら使用。
---

# 新しい記事を追加する

このサイトは静的HTMLサイト。記事を1本足すには複数ファイルを揃った形で更新する必要がある。
このスキルはその手順を抜け漏れなく実行するためのもの。

## 入力として確認すること
- 記事のテーマ（ユーザー指定。未指定ならどんな切り口か聞く）
- 公開日（指定がなければ今日の日付）

## ブランドの前提（必ず守る）
- 運営: AIdollargame、署名は「AIdollargame 編集部」
- ビジョン: **「作業はAIに、愛は人間に」**（AIが役割仕事を担い、人間が人間らしい時間を取り戻す）。記事は必ずこのビジョンに絡める。
- 読者: 日本の中小企業の経営者・実務者（B2B）
- トーン: 丁寧・断定しすぎない・煽らない。AIを過度に隠したり恐怖を煽る表現は避ける。

## 記事HTMLの作り方
**テンプレートの正本は `scripts/generate_articles.py` の `ARTICLE_HTML` 文字列**。これと完全に同じ構造で作ること（メタタグ・OGタグ・Twitterカード・JSON-LD schema・CSS・nav・cta・related・footer をそのまま踏襲）。

差し込む値:
| プレースホルダ | 中身 | 例 |
|---|---|---|
| `slug` | 英数字とハイフンのみのファイル名 | `gpt5-japan-impact` |
| `title` | 日本語タイトル30字以内 | |
| `description` | カード説明60字以内 | |
| `date` | 表示用日付 `YYYY / MM / DD` | `2026 / 06 / 02` |
| `date_iso` | メタ用日付 `YYYY-MM-DD` | `2026-06-02` |
| `body` | 本文HTML | 下記 |

本文(`body`)の要件:
- 600〜800字程度
- `<h2>` を2〜3個（CSSで左に水色の縦線が付く）
- `<blockquote><p>...</p></blockquote>` を1個（印象的な一文）
- 重要語は `<strong>` で強調
- 段落は `<p>`
- 末尾でビジョン「作業はAIに、愛は人間に」と必ず結びつける

保存先: `articles/{slug}.html`

## 一覧ページへのカード追加（2か所）

### 1. 記事一覧 `articles/index.html`
`<!-- AUTO-ARTICLES-START -->` の直後に、新しい順で次の形のカードを挿入する（`make_card_articles_index` と同形）:
```html
    <a href="./{slug}.html" class="article-card" data-tag="news">
      <div class="card-color-bar accent"></div>
      <div class="card-body">
        <div class="card-tag accent">NEWS</div>
        <div class="card-date">{date}</div>
        <div class="card-title">{title}</div>
        <div class="card-desc">{description}</div>
        <div class="card-link">READ MORE →</div>
      </div>
    </a>
```

### 2. トップ `index.html`
`<!-- ARTICLES-GRID-START -->` 〜 `<!-- ARTICLES-GRID-END -->` の間の先頭に、次の形で追加（`make_card_main_index` と同形）。トップは件数を絞っているので、古いカードが多すぎる場合は末尾を整理する:
```html
    <a href="./articles/{slug}.html" class="article-card">
      <div class="article-body-inner">
        <div class="article-cat">NEWS</div>
        <div class="article-date">{date}</div>
        <div class="article-title-card">{title}</div>
        <div class="article-desc">{description}</div>
        <div class="article-link">READ MORE →</div>
      </div>
    </a>
```

## sitemap.xml への登録（重要・忘れがち）
`scripts/generate_articles.py` はsitemapを更新しない。手動で `sitemap.xml` の `</urlset>` の直前に追記する:
```xml
  <url>
    <loc>https://aidollargame.com/articles/{slug}.html</loc>
    <lastmod>{date_iso}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
```
既存記事の `lastmod` 形式（`YYYY-MM-DD`）に合わせること。

## OG画像（任意だが推奨）
記事テンプレートの `og:image` / `twitter:image` は既定で `og-default.png` を指す。
記事専用のOG画像を作る場合は **`og-image` スキル** を使い、生成後に記事HTMLの該当URLを `https://aidollargame.com/og-articles-{slug}.png` に差し替える。

## 仕上げ
1. ブラウザ確認できる場合は `articles/{slug}.html` を開いてレイアウト崩れがないか見る
2. 変更をまとめてコミット（記事HTML / articles/index.html / index.html / sitemap.xml）。コミットメッセージは日本語で「記事追加: {title} ({YYYY/MM/DD})」の形
3. ユーザーが望めばプッシュ

## チェックリスト
- [ ] `articles/{slug}.html` を作成（テンプレ準拠・ビジョンに接続）
- [ ] `articles/index.html` にカード追加
- [ ] `index.html` にカード追加
- [ ] `sitemap.xml` に `<url>` 追加
- [ ] (任意) OG画像を作って差し替え
- [ ] コミット
