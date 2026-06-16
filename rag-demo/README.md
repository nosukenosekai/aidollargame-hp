# RAG Demo（触れるRAGデモ）

完全クライアントサイドで動くRAGデモ。GitHub Pages上でそのまま動く。

URL: `/rag-demo/`

## このデモの構成

| 要素 | 実装 |
|------|------|
| ホスティング | GitHub Pages（既存） |
| 知識ベース | `data.js` に18件のサンプル（架空の介護事業所） |
| 検索 | 文字バイグラム + BM25（純JS、サーバー不要） |
| 回答生成 | テンプレート（検索結果を整形） |
| コスト | **完全無料・APIキー不要** |

LLM を呼んでいないので、回答はテンプレート（検索ヒットの整形）。営業用に「触れる雰囲気」を見せる目的としては十分。

## 本番（顧客案件）にアップグレードする時

### Step 1: LLM を入れる（Cloudflare Workers AI / 無料枠）

`wrangler init rag-worker` → `src/index.ts`:

```ts
export interface Env {
  AI: Ai;
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    if (req.method !== 'POST') return new Response('Method Not Allowed', { status: 405 });
    const { question, contexts } = await req.json();

    const prompt = `以下は社内資料からの抜粋です。これだけを根拠にして、質問に丁寧に答えてください。

[社内資料]
${contexts.map((c: string, i: number) => `(${i+1}) ${c}`).join('\n\n')}

[質問]
${question}

[回答]`;

    const result = await env.AI.run('@cf/meta/llama-3.1-8b-instruct', {
      prompt,
      max_tokens: 512,
    });

    return Response.json({ answer: result.response });
  }
};
```

`wrangler.toml`:
```toml
name = "rag-worker"
main = "src/index.ts"
compatibility_date = "2025-01-01"

[ai]
binding = "AI"
```

→ `wrangler deploy` → 月10万リクエストまで完全無料。

そして `index.html` の `ask()` の中身を：

```js
const res = await fetch('https://rag-worker.YOUR-SUBDOMAIN.workers.dev', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question: q,
    contexts: hits.slice(0,3).map(h => h.doc.text)
  })
});
const { answer } = await res.json();
```

これで本物のLLM回答に切り替わる。

### Step 2: 顧客データを差し替える

`data.js` を顧客から提供されたデータに置き換える。フォーマット:

```js
const DATA = [
  { source: "資料名", section: "章/節", text: "本文..." },
  ...
];
```

文書が多くなったら（数百〜数千件）、ベクトル化してCloudflare Vectorize（無料枠あり）に乗せる。

### Step 3: 品質を上げたい時

- LLMをClaude API（Anthropic）に差し替え（月数千円〜）
- 埋め込みベクトルに変更（`@cf/baai/bge-base-en-v1.5` または日本語埋め込み）
- 評価セット作成 → モデル比較の自動評価（private eval）

## 顧客案件の進め方

1. NDA締結
2. データの種類・量・更新頻度のヒアリング
3. ベースのRAG構築（このリポジトリのコードがそのまま使える）
4. 顧客環境にデプロイ（Cloudflare or 顧客クラウド）
5. 月次で評価・改善（使うほど賢くなるloop）

## ライセンス

社内利用。サンプルデータは架空。
