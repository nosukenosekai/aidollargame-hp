# CLAUDE.md

このファイルは Claude Code がこのリポジトリで作業するときの前提知識です。
作業前に必ず目を通し、変更時は実態に合わせて更新してください。

## このプロジェクトは何か

**株式会社AIdollargame の公式サイト**（https://aidollargame.com/）。
GitHub Pages でホスティングされる**静的サイト**で、ビルド工程はありません。
HTML/CSS/JS を直接編集し、push するとそのまま公開されます。

- ビルドツール・npm・フレームワークなし（`package.json` は存在しない）
- `CNAME` = `aidollargame.com`（独自ドメイン）
- `.nojekyll` あり（Jekyll 処理を無効化＝ファイルをそのまま配信）

> 補足: 会社はB2BのAI導入支援・コンサルティング企業。社名に「アイドル/ゲーム」が
> 入るがエンタメ事業とは無関係。法人番号 1011101111386 で一意識別される（同一住所の
> 他テナント企業との資本・人的関係はない）。詳細は `llms.txt` を参照。

## ディレクトリ構成

| パス | 内容 |
|------|------|
| `index.html` | トップページ |
| `*.html`（ルート） | 主要ページ（ai-consulting, aiside, human-clone-ai, line-ai-agent, shindan 等） |
| `articles/` | 記事ページ（1記事 = 1 HTML）。`index.html` が記事一覧、`_articles_index.json` がメタ索引 |
| `content/note/`, `content/clips/` | 記事の元になる下書き Markdown（日付ファイル名） |
| `scripts/` | `generate_articles.py`（週次記事自動生成）、`generate_ogp.py`（OGP画像生成） |
| `rag-demo/` | 完全クライアントサイドの RAG デモ（営業用。`README.md` に本番化手順あり） |
| `logos/` | ロゴ素材 |
| `llms.txt` | LLM/AI検索向けの会社情報まとめ（AIO最適化の要） |
| `sitemap.xml` / `robots.txt` | SEO |
| `.github/workflows/auto-articles.yml` | 週次記事生成の GitHub Actions |

## ページ HTML の規約（記事を手で追加・編集するとき）

各ページは独立した完結HTMLで、共通テンプレートのインクルードはありません。
新規ページを作るときは既存ページ（例: `articles/about-aidollargame.html`）を
コピーして、以下を**必ず**そろえる:

1. `<title>` … `〇〇 | AIdollargame` 形式
2. `<meta name="description">`
3. `<link rel="canonical">` … 絶対URL
4. OGP（`og:title` / `og:description` / `og:url` / `og:image`）と Twitter Card
5. `<script type="application/ld+json">` の構造化データ（Article / Organization）
6. ファビコン群への相対パス（`articles/` 配下は `../favicon...`）

記事を追加したら手動で更新するもの:
- `articles/_articles_index.json`（slug / date / title）
- `articles/index.html` の記事一覧カード
- `index.html` のトップ記事グリッド
- `sitemap.xml`（新URLの追加）
- 必要に応じて `llms.txt`（重要ページはここにも載せるとAI検索に拾われやすい）

slug は小文字英数字とハイフンのみ（`^[a-z0-9][a-z0-9-]{0,79}$`）。

## 記事の自動生成（週次）

`.github/workflows/auto-articles.yml` が毎週月曜 00:00 UTC に
`scripts/generate_articles.py` を実行 → Google News RSS を取得 →
Claude（`anthropic` SDK、現在 `model="claude-opus-4-5"`）で記事生成 →
`articles/` に保存し索引・トップを自動更新して push する。

セキュリティ上重要な前提（スクリプト改変時は壊さないこと）:
- 生成記事は**人手レビューなしで自動公開**される。RSS由来の untrusted な入力を
  LLM が処理するため、出力は信頼できないものとして扱う。
- `generate_articles.py` の `sanitize_article` / `_BodySanitizer` で
  slug 検証（パストラバーサル防止）、title/description のエスケープ、
  body HTML のタグ allowlist サニタイズを行っている。**この防御を弱めない**。
- 自動生成は `articles/index.html` と `index.html` の HTML コメントマーカー
  （`<!-- AUTO-ARTICLES-START -->`, `<!-- ARTICLES-GRID-START/END -->`）を
  目印に挿入する。これらのマーカーを消さない。

ローカル実行例: `ANTHROPIC_API_KEY=... python scripts/generate_articles.py`
（依存: `pip install anthropic feedparser`）

## 動作確認

ビルド不要。ローカルで見るだけなら任意の静的サーバで十分:

```
python3 -m http.server 8000   # → http://localhost:8000/
```

## このリポジトリでの作業方針

- 文章はすべて日本語。トーン丁寧（ですます）。既存記事の語り口に合わせる。
- 余計なフレームワーク導入や全面リライトはしない。最小差分で。
- コミットメッセージは日本語で、何をしたかが分かる粒度（既存ログに倣う）。
