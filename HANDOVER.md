# リポジトリ移管 引き継ぎチェックリスト

`setouchi-h/aidollargame-hp` → **`nosukenosekai/aidollargame-hp`** への移管に伴う作業メモ。

移管そのもの（オーナー変更）は完了済み。ただし GitHub の仕様上、**リポジトリと一緒に自動では引き継がれない設定** があるため、以下を新オーナー側で手動再設定する必要があります。

---

## 1. コード側の状況（対応不要 ✅）

- ソースコード内に旧オーナー（`setouchi-h`）への参照は **ゼロ**。
- サイトは独自ドメイン **`aidollargame.com`**（`CNAME` に記載）で運用。
- canonical / og:url / 構造化データ・sitemap.xml のURLは全て `https://aidollargame.com/...` に統一済み。`github.io` へのハードコード無し。

→ **URL・参照の書き換えは不要**。オーナーが変わっても静的サイトの中身はそのまま動きます。

---

## 2. 手動で再設定が必要なもの（要対応 ⚠️）

GitHub は移管時に以下を引き継ぎません（移管確認メールにも記載）。新リポジトリの Settings で再設定してください。

### 2-1. Actions Secrets（最重要）
移管でシークレットは **全て消えます**。これが無いと下記の自動ワークフローが失敗します。
`Settings → Secrets and variables → Actions → New repository secret` で再登録：

| ワークフロー | 必要な Secret |
|---|---|
| `auto-articles.yml`（週次AI記事自動生成 / 毎週月 09:00 JST） | `GEMINI_API_KEY` |
| `reminders.yml`（リマインドメール 朝夜） | `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS` / `MAIL_TO` / `MAIL_FROM` |

> ※ 値は旧環境と同じものを再投入。SMTP 認証情報・Gemini APIキーは手元の控えから。

### 2-2. Actions の書き込み権限
`auto-articles.yml` は生成記事を **自分でコミット＆push** します。
`Settings → Actions → General → Workflow permissions` を **「Read and write permissions」** に設定。
（移管直後は Actions が無効化されている場合があるので、同画面で有効化も確認）

### 2-3. GitHub Pages / 独自ドメイン
- `Settings → Pages` で公開ブランチ（`main` / ルート）を再指定。
- Custom domain に **`aidollargame.com`** を設定し、`Enforce HTTPS` を有効化。
- アカウント設定側で独自ドメインの **Verify（所有者確認）** を実施。
- ⚠️ このリポジトリは **Private**。Private リポジトリの Pages 公開は **有料プラン（Pro 以上）が必要**。移管確認メールでも「既存 Pages を失う可能性」が警告されていたため、無料プランのままだと公開されない点に注意。
- DNS（`aidollargame.com` の A / CNAME レコード）は GitHub Pages 向けのまま変更不要のはずだが、Pages を再有効化後に **実際に表示されるか** を必ず確認。

### 2-4. その他（利用していれば再設定）
- Branch / tag の保護ルール（移管で消失）
- CODEOWNERS、Wiki、Draft PR、複数アサイン／複数レビュアー等（プラン依存機能）

---

## 3. 移管後の動作確認チェック

- [ ] Secrets を全て再登録した
- [ ] Actions を有効化し、Workflow permissions を Read and write にした
- [ ] `auto-articles.yml` を `workflow_dispatch` で手動実行 → 記事生成＆push が成功
- [ ] `reminders.yml` を `workflow_dispatch` で手動実行 → リマインドメールが届く
- [ ] Pages を再設定し `https://aidollargame.com/` が正しく表示される
- [ ] `Enforce HTTPS` が有効
