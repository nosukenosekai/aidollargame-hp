---
name: og-image
description: AIdollargame(aidollargame.com)のOG画像/サムネイル(1200x630, サマーウォーズ調 navy+cyan/blue+red)を生成・差し替えするときに使う。新しい記事やページのSNSシェア画像を作る、既存のサムネイルを作り直すときに使用。「OG画像作って」「サムネ作り直して」と言われたら使用。
---

# OG画像・サムネイルを作る

SNSでシェアされたときに表示される 1200×630 の画像を生成する。
正本スクリプトは **`scripts/generate_ogp.py`**（Pillowで描画）。デザインはサマーウォーズ調（濃紺の背景＋水色/青のグロー＋赤の差し色、左に縦アクセント線、ロゴ、右下にURL）。

## 前提（環境）
- 必要ライブラリ: Pillow。未導入なら `pip install Pillow`（ローカル処理・課金なし。確認プロンプトが出たら許可）。
- 日本語フォントはOS横断で自動解決される（macOSのヒラギノ → Linux/CIのNoto CJK → wqy-zenhei）。
  CI(GitHub Actions)で実行する場合はNotoかwqyのCJKフォントが必要。無い環境では
  `apt-get install -y fonts-noto-cjk` などを足す。
- 出力先はリポジトリ直下（`OUTPUT_DIR`）。ファイル名は `og-*.png`。

## 1枚足す/差し替える手順
`scripts/generate_ogp.py` の `main()` 内に1行 `render_card(...)` を追加（または既存行を編集）する。

```python
render_card(
    "メインの見出し（記事タイトルなど）",   # title
    "サブの一文 or カテゴリ（INSIGHT 等）",  # subtitle（不要なら "" ）
    "og-articles-{slug}.png",               # 出力ファイル名
    title_size=56,                          # 長いタイトルは小さめ(50-58)、短いものは大きめ(72-104)
)
```

命名規則（既存に合わせる）:
- トップ: `og-default.png`
- プロダクトLP: `og-aiside.png` / `og-human-clone-ai.png` / `og-line-ai-agent.png`
- 記事: `og-articles-{slug}.png`

`render_card` の挙動メモ:
- タイトルは自動で折り返し、3行を超えると自動で縮小する（`title_size` は上限の目安）
- 日本語の禁則（行頭・行末の約物）は `wrap_text` が処理済み
- `subtitle` は水色で1行表示

## 実行
```bash
python3 scripts/generate_ogp.py
```
`main()` に書かれた全カードを再生成する（既存pngは上書き）。特定の1枚だけ確認したいときは、生成後に画像を開いて目視確認する。

## 記事HTMLへの反映
記事専用のOG画像を作ったら、その記事HTMLの2か所のURLを差し替える:
- `<meta property="og:image" content="https://aidollargame.com/og-articles-{slug}.png">`
- `<meta name="twitter:image" content="https://aidollargame.com/og-articles-{slug}.png">`
（既定は `og-default.png` なので、専用画像を作った記事だけ書き換える）

## 仕上げ
1. 生成した `og-*.png` を開いて、文字切れ・はみ出し・読みづらさがないか確認
2. 画像と、差し替えた記事HTMLをコミット（メッセージは日本語で「OG画像追加/差し替え: {対象}」）
3. ユーザーが望めばプッシュ

## チェックリスト
- [ ] Pillow導入済み
- [ ] `main()` に `render_card(...)` を追加/編集
- [ ] `python3 scripts/generate_ogp.py` 実行
- [ ] 画像を目視確認（文字切れ無し）
- [ ] 記事の `og:image`/`twitter:image` を差し替え（記事用の場合）
- [ ] コミット
