# メモ：Mac でローカルの Claude Code を動かす（2026-08-19）

**目的**：claude.ai/code（リモート）はネットワークが GitHub とパッケージ管理系に限定されていて、
Figma はもちろん外部サイトを一切見に行けない。**ローカルなら制限がないので、Claude がブラウザを操作して直接デザインを見られる。**
Tak が Codex でやっているのと同じ形。

## 手順

### 1. Claude Code を入れる

```
curl -fsSL https://claude.ai/install.sh | bash
claude --version
```

- macOS 13（Ventura）以降。Node.js は不要（自己完結型のバイナリが入る）。
- うまく入らない時は `claude doctor` で状態を確認する。
- npm 派なら `npx @anthropic-ai/claude-code`、Homebrew 派なら `brew install claude-code`（コミュニティ tap）。

### 2. このリポジトリを持ってくる

```
git clone https://github.com/nosukenosekai/aidollargame-hp.git
cd aidollargame-hp
claude
```

初回は認証を求められるのでブラウザでログインする。

### 3. ブラウザ操作を有効にする（Playwright MCP）

```
claude mcp add playwright npx @playwright/mcp@latest
```

**ログインのやり方（ここが肝）**

- Claude に「Figma を開いて」と頼むと、**目に見えるブラウザウィンドウが立ち上がる**。
- そこで**自分でログインする**。以降そのプロファイルは保持されるので、毎回ログインし直す必要はない。
- **パスワードを Claude に渡す必要はない。** 画面を出させて、自分の手で入力するだけ。

**やらなくていいこと**：既存の Chrome プロファイルに繋ぎに行く方法もあるが、
Chrome 136 以降は既定プロファイルでのリモートデバッグを塞いでいて、プロファイルのコピーなど手間が増える。
**上の「立ち上がったウィンドウで一度ログインする」で十分。**

## 注意

- Claude が操作するブラウザは**ログイン済みのセッションを持つ**。
  ネットバンキングや管理画面など機微なものに入っているプロファイルは使わない。
  **AI 操作用に専用プロファイルを分けるのが安全。**
- リモート（claude.ai/code）とローカルは**同じリポジトリの同じブランチを共有できる**。
  作業前に `git pull`、作業後に `git push` を忘れない。

## これで何ができるようになるか

- Figma のコミュニティテンプレートを **Claude 自身が開いて見て**、配色・余白・文字組みを読み取れる。
- スクショを貼る作業が不要になる。
- Figma に限らず、参考サイトを直接見に行ける。

## 出典

検索で確認（2026-08-19）。詳細は各記事を参照。
