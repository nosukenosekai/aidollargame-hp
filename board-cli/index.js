#!/usr/bin/env node
/**
 * 仮想役員会CLI（Gemini版 / 無料枠で動く）
 *
 * 相談を投げると、立場(レンズ)の違う5人の役員が議論して、結論を1つに絞る。
 *
 *   役員の発言   : gemini-2.5-flash (速い・並列・無料枠が緩め)
 *   最終まとめ   : gemini-2.5-pro   (1回だけ)
 *
 * モデルは環境変数で差し替え可:
 *   GEMINI_MEMBER_MODEL  / GEMINI_SUMMARY_MODEL
 *
 * 役員は「役割(レンズ)」で定義する。名前はただのラベルで、本人の実発言は再現しない。
 * 数字や固有事実には必ず [要裏取り] を付けさせる。
 */

import { GoogleGenAI } from "@google/genai";
import { readFile, readdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join, resolve } from "node:path";
import readline from "node:readline";

const __dirname = dirname(fileURLToPath(import.meta.url));
const BOARDS_DIR = join(__dirname, "boards");

const MODEL_MEMBER = process.env.GEMINI_MEMBER_MODEL || "gemini-2.5-flash";
const MODEL_SUMMARY = process.env.GEMINI_SUMMARY_MODEL || "gemini-2.5-pro";

// ── 端末の色付け（依存を増やさず最小限）─────────────────────────
const C = {
  reset: "\x1b[0m",
  dim: "\x1b[2m",
  bold: "\x1b[1m",
  cyan: "\x1b[36m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  red: "\x1b[31m",
  magenta: "\x1b[35m",
  blue: "\x1b[34m",
};
const paint = (s, color) => `${color}${s}${C.reset}`;
const palette = [C.cyan, C.green, C.yellow, C.magenta, C.blue, C.red];

function hr(char = "─") {
  return paint(char.repeat(60), C.dim);
}
function header(text, color = C.bold) {
  console.log("\n" + hr());
  console.log(paint(text, C.bold + color));
  console.log(hr());
}

// ── 全役員に固定で入れる「お前はレンズであって本人ではない」制約 ──
const LENS_RULE = [
  "【絶対の前提】お前は思考の『レンズ(型)』であって、ラベルにある人物本人ではない。",
  "本人が実際にこう言った・こう考えていると書くな。本人の発言の引用や再現もするな。",
  "あくまでその役割が持つ『考え方の型』だけを借りて、お前自身の言葉で意見を述べろ。",
  "数字・金額・割合・市場規模・固有名詞などの具体的な事実を出したら、その直後に必ず [要裏取り] と付けろ。",
  "推測やたとえ話で出した数字にも [要裏取り] を付けろ。確証のない事実を断定するな。",
].join("\n");

function memberSystemPrompt(member) {
  return [
    LENS_RULE,
    "",
    `お前の役割(レンズ): ${member.role}`,
    `最優先する価値観: ${member.priority}`,
    `口調・スタンス: ${member.tone}`,
    member.skeptic
      ? "お前は悪魔の代弁者だ。同意するな。常に穴とリスクを探し、誰も言いたがらない反論を言え。"
      : "自分のレンズに正直に。八方美人になるな。立場をはっきりさせろ。",
    "",
    "出力は日本語。前置きや自己紹介は不要。要点を先に、簡潔に。",
  ].join("\n");
}

// ── Gemini 呼び出しの薄いラッパ ─────────────────────────────────
async function ask(client, { model, system, prompt, maxTokens = 1024 }) {
  const res = await client.models.generateContent({
    model,
    contents: prompt,
    config: {
      systemInstruction: system,
      maxOutputTokens: maxTokens,
    },
  });
  return (res.text || "").trim();
}

// ── ラウンド1: 各役員が自分のレンズで意見を出す（並列）──────────
async function roundOpinions(client, board, topic, premises) {
  const ctx = buildContext(topic, premises);
  const tasks = board.members.map((m) =>
    ask(client, {
      model: MODEL_MEMBER,
      system: memberSystemPrompt(m),
      prompt:
        `${ctx}\n\n` +
        "上の相談について、お前のレンズから見た意見を述べろ。\n" +
        "・結論(賛成/反対/条件付き)を最初に一言で\n" +
        "・その理由を3点まで\n" +
        "・お前の価値観から見て一番大事な論点を1つ",
      maxTokens: 900,
    }).then((text) => ({ member: m, text }))
  );
  return Promise.all(tasks);
}

// ── ラウンド2: 他4人の意見を渡して反論させる（並列）────────────
async function roundRebuttals(client, board, topic, premises, opinions) {
  const ctx = buildContext(topic, premises);
  const tasks = board.members.map((m) => {
    const others = opinions
      .filter((o) => o.member.id !== m.id)
      .map((o) => `■ ${o.member.label}(${o.member.role})の意見:\n${o.text}`)
      .join("\n\n");
    return ask(client, {
      model: MODEL_MEMBER,
      system: memberSystemPrompt(m),
      prompt:
        `${ctx}\n\n` +
        "他の役員の意見は以下の通りだ。\n\n" +
        `${others}\n\n` +
        "これらに対して、お前のレンズから反論・補強をしろ。\n" +
        "・最も同意できない意見はどれで、なぜ間違い/危ういか\n" +
        "・逆に乗れる意見と、その上で足したい視点\n" +
        "・議論を踏まえてお前の結論は変わるか、変わらないか",
      maxTokens: 900,
    }).then((text) => ({ member: m, text }));
  });
  return Promise.all(tasks);
}

// ── ラウンド3: 懐疑派に「最大の懸念を1つだけ」言わせる ──────────
async function roundBiggestConcern(client, board, topic, premises, opinions, rebuttals) {
  const skeptic = board.members.find((m) => m.skeptic) || board.members[0];
  const ctx = buildContext(topic, premises);
  const transcript = renderTranscriptForModel(opinions, rebuttals);
  const text = await ask(client, {
    model: MODEL_MEMBER,
    system: memberSystemPrompt(skeptic),
    prompt:
      `${ctx}\n\n` +
      "ここまでの全議論:\n" +
      `${transcript}\n\n` +
      "この判断における『最大の懸念』を、たった1つだけに絞って言え。\n" +
      "複数挙げるな。最も致命的な1点だけ。\n" +
      "・懸念(1文)\n・それが現実になる条件\n・最低限の確認方法",
    maxTokens: 500,
  });
  return { member: skeptic, text };
}

// ── ラウンド4: gemini-pro に全部渡して結論を1つに強制 ──────────────
async function roundFinalDecision(client, board, topic, premises, opinions, rebuttals, concern) {
  const ctx = buildContext(topic, premises);
  const transcript = renderTranscriptForModel(opinions, rebuttals);
  const system = [
    "お前は仮想役員会の議長だ。役員たちは『思考のレンズ』であり実在人物本人ではない。本人の発言として扱うな。",
    "数字・金額・割合・固有事実を書いたら直後に必ず [要裏取り] を付けろ。",
    "玉虫色の結論を出すな。やるか/やらないか/何を変えてやるかを1つに決めきれ。",
  ].join("\n");
  const text = await ask(client, {
    model: MODEL_SUMMARY,
    system,
    prompt:
      `${ctx}\n\n` +
      "役員会の議論(意見→反論):\n" +
      `${transcript}\n\n` +
      `懐疑派が挙げた最大の懸念:\n${concern.text}\n\n` +
      "以上の議論を踏まえ、『私が今日決めるべきこと』を1つに絞って結論を出せ。\n\n" +
      "次の形式で:\n" +
      "1. 今日の決定(1文・断定): \n" +
      "2. なぜこれか(議論のどこを採ったか・3点まで): \n" +
      "3. 最大の懸念への手当て(1つ): \n" +
      "4. 最初の一歩(明日できる具体行動1つ): \n" +
      "5. 撤回・見直しの条件(これが起きたら考え直す): ",
    maxTokens: 1200,
  });
  return text;
}

// ── 文脈の組み立て（相談文＋差し込まれた前提）──────────────────
function buildContext(topic, premises) {
  let ctx = `【相談】\n${topic}`;
  if (premises.length) {
    ctx +=
      "\n\n【追加で踏まえる前提】\n" +
      premises.map((p, i) => `(${i + 1}) ${p}`).join("\n");
  }
  return ctx;
}

function renderTranscriptForModel(opinions, rebuttals) {
  const lines = [];
  lines.push("=== 各役員の意見 ===");
  for (const o of opinions) {
    lines.push(`【${o.member.label} / ${o.member.role}】\n${o.text}`);
  }
  lines.push("\n=== 相互の反論 ===");
  for (const r of rebuttals) {
    lines.push(`【${r.member.label} / ${r.member.role}】\n${r.text}`);
  }
  return lines.join("\n\n");
}

// ── 端末への表示 ────────────────────────────────────────────────
function printSection(title, items, colorBase = 0) {
  header(title);
  items.forEach((it, i) => {
    const color = palette[(i + colorBase) % palette.length];
    console.log(
      "\n" + paint(`● ${it.member.label}`, C.bold + color) +
        paint(`  (${it.member.role})`, C.dim)
    );
    console.log(indent(it.text));
  });
}

function indent(text, pad = "  ") {
  return text
    .split("\n")
    .map((l) => pad + l)
    .join("\n");
}

// ── 役員会1回分の実行 ──────────────────────────────────────────
async function runBoard(client, board, topic, premises) {
  console.log(
    paint(`\n▶ board: ${board.title} (${board.name}) / 役員 ${board.members.length}名`, C.dim)
  );
  if (premises.length) {
    console.log(paint(`▶ 追加前提 ${premises.length}件を反映`, C.dim));
  }

  process.stdout.write(paint("\n…各役員が意見を出しています(並列)\n", C.dim));
  const opinions = await roundOpinions(client, board, topic, premises);
  printSection("① 各役員の意見", opinions);

  process.stdout.write(paint("\n…お互いに反論させています(並列)\n", C.dim));
  const rebuttals = await roundRebuttals(client, board, topic, premises, opinions);
  printSection("② 相互の反論", rebuttals);

  process.stdout.write(paint("\n…懐疑派が最大の懸念を絞っています\n", C.dim));
  const concern = await roundBiggestConcern(
    client, board, topic, premises, opinions, rebuttals
  );
  header("③ 最大の懸念（懐疑派）", C.red);
  console.log(
    "\n" + paint(`● ${concern.member.label}`, C.bold + C.red) +
      paint(`  (${concern.member.role})`, C.dim)
  );
  console.log(indent(concern.text));

  process.stdout.write(paint("\n…議長(gemini-pro)が結論を1つに絞っています\n", C.dim));
  const decision = await roundFinalDecision(
    client, board, topic, premises, opinions, rebuttals, concern
  );
  header("④ 最終結論（議長 / gemini-pro）", C.green);
  console.log("\n" + indent(paint(decision, C.bold)));
  console.log(
    "\n" + paint("※ [要裏取り] が付いた数字・事実は、決定前に必ず裏を取ること。", C.yellow)
  );

  return { opinions, rebuttals, concern, decision };
}

// ── board の読み込み ────────────────────────────────────────────
async function loadBoard(boardArg) {
  // パス指定ならそのまま、名前指定なら boards/<name>.json
  let path;
  if (!boardArg) {
    path = join(BOARDS_DIR, "default.json");
  } else if (boardArg.endsWith(".json") || boardArg.includes("/")) {
    path = resolve(boardArg);
  } else {
    path = join(BOARDS_DIR, `${boardArg}.json`);
  }
  if (!existsSync(path)) {
    throw new Error(`board が見つかりません: ${path}`);
  }
  const board = JSON.parse(await readFile(path, "utf8"));
  if (!Array.isArray(board.members) || board.members.length === 0) {
    throw new Error(`board の members が不正です: ${path}`);
  }
  board.name = board.name || boardArg || "default";
  board.title = board.title || board.name;
  return board;
}

async function listBoards() {
  const files = (await readdir(BOARDS_DIR)).filter((f) => f.endsWith(".json"));
  const boards = [];
  for (const f of files) {
    try {
      const b = JSON.parse(await readFile(join(BOARDS_DIR, f), "utf8"));
      boards.push({
        name: b.name || f.replace(/\.json$/, ""),
        title: b.title || "",
        description: b.description || "",
        count: (b.members || []).length,
      });
    } catch {
      /* skip broken */
    }
  }
  return boards;
}

// ── 引数パース ──────────────────────────────────────────────────
function parseArgs(argv) {
  const out = { board: null, topic: null, premises: [], list: false, help: false, once: false };
  const rest = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--board" || a === "-b") out.board = argv[++i];
    else if (a === "--premise" || a === "-p") out.premises.push(argv[++i]);
    else if (a === "--list" || a === "-l") out.list = true;
    else if (a === "--once") out.once = true;
    else if (a === "--help" || a === "-h") out.help = true;
    else rest.push(a);
  }
  if (rest.length) out.topic = rest.join(" ");
  return out;
}

function printHelp() {
  console.log(`
仮想役員会CLI — 立場の違う5人が議論して結論を1つ出す

使い方:
  node index.js [options] "相談文"

オプション:
  -b, --board <name|path>   使う board を指定 (例: -b saiyo, -b ./my.json)
  -p, --premise "<前提>"    踏まえる前提を差し込む(複数可)
  -l, --list                利用できる board 一覧を表示
      --once                対話モードに入らず1回で終了
  -h, --help                このヘルプ

例:
  node index.js "新規事業に1000万投資すべきか"
  node index.js -b neage "主力プランを20%値上げすべきか"
  node index.js -b saiyo -p "現場の人数が足りていない" "シニアを採るべきか"

対話モード:
  実行後、追加の前提を打ち込むと、それを反映して「もう一回」議論できる。
    例) 現場の人数が足りてない前提で再実行
  コマンド: :board <name> で board 切替 / :reset 前提クリア / :show 前提表示
           :quit または空 Enter で終了

環境変数:
  GEMINI_API_KEY        (必須)  Google AI Studio の無料APIキー
                                 https://aistudio.google.com/apikey
  GEMINI_MEMBER_MODEL   (任意)  役員の発言モデル (既定: gemini-2.5-flash)
  GEMINI_SUMMARY_MODEL  (任意)  最終まとめモデル (既定: gemini-2.5-pro)
`);
}

// ── 対話モード ──────────────────────────────────────────────────
async function interactive(client, state) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const question = (q) => new Promise((res) => rl.question(q, res));

  console.log(
    paint(
      "\n― 対話モード ― 追加前提を入力して Enter で再実行。" +
        " :help でコマンド一覧、空 Enter / :quit で終了。",
      C.dim
    )
  );

  for (;;) {
    const line = (await question(paint("\n前提を追加 > ", C.bold))).trim();
    if (line === "" || line === ":quit" || line === ":q") break;

    if (line === ":help") {
      console.log(
        [
          "  :board <name>   board を切り替える (例 :board saiyo)",
          "  :list          board 一覧",
          "  :reset         追加前提をすべてクリア",
          "  :show          いまの前提を表示",
          "  :quit          終了",
          "  それ以外の入力 はすべて『追加前提』として再実行されます",
        ].join("\n")
      );
      continue;
    }
    if (line === ":reset") {
      state.premises = [];
      console.log(paint("前提をクリアしました。", C.dim));
      continue;
    }
    if (line === ":show") {
      if (!state.premises.length) console.log(paint("（前提なし）", C.dim));
      else state.premises.forEach((p, i) => console.log(`  (${i + 1}) ${p}`));
      continue;
    }
    if (line === ":list") {
      const boards = await listBoards();
      boards.forEach((b) =>
        console.log(`  ${paint(b.name, C.cyan)}  ${b.title} — ${b.description}`)
      );
      continue;
    }
    if (line.startsWith(":board")) {
      const name = line.split(/\s+/)[1];
      if (!name) {
        console.log(paint("使い方: :board <name>", C.yellow));
        continue;
      }
      try {
        state.board = await loadBoard(name);
        console.log(paint(`board を ${state.board.title} に切り替えました。`, C.green));
      } catch (e) {
        console.log(paint(`切替失敗: ${e.message}`, C.red));
      }
      continue;
    }

    // 通常の入力 = 追加前提として再実行
    state.premises.push(line);
    try {
      await runBoard(client, state.board, state.topic, state.premises);
    } catch (e) {
      console.log(paint(`実行エラー: ${e.message}`, C.red));
    }
  }
  rl.close();
}

// ── メイン ──────────────────────────────────────────────────────
async function main() {
  const args = parseArgs(process.argv.slice(2));

  if (args.help) {
    printHelp();
    return;
  }
  if (args.list) {
    const boards = await listBoards();
    header("利用できる board");
    boards.forEach((b) =>
      console.log(
        `  ${paint(b.name.padEnd(10), C.cyan)} ${b.title}  ${paint("(" + b.count + "名)", C.dim)}\n` +
          `             ${paint(b.description, C.dim)}`
      )
    );
    return;
  }

  const apiKey = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;
  if (!apiKey) {
    console.error(
      paint(
        "環境変数 GEMINI_API_KEY が設定されていません。\n" +
          "https://aistudio.google.com/apikey で無料のキーを取得して設定してください。",
        C.red
      )
    );
    process.exit(1);
  }

  const board = await loadBoard(args.board);

  let topic = args.topic;
  if (!topic) {
    // 相談文が無ければ対話で1問もらう
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    topic = await new Promise((res) =>
      rl.question(paint("相談を入力してください > ", C.bold), (a) => {
        rl.close();
        res(a.trim());
      })
    );
    if (!topic) {
      console.error(paint("相談文が空です。", C.red));
      process.exit(1);
    }
  }

  const client = new GoogleGenAI({ apiKey });
  const state = { board, topic, premises: [...args.premises] };

  await runBoard(client, state.board, state.topic, state.premises);

  if (!args.once) {
    await interactive(client, state);
  }
  console.log(paint("\nおつかれさまでした。", C.dim));
}

main().catch((e) => {
  console.error(paint(`\nエラー: ${e.message}`, C.red));
  process.exit(1);
});
