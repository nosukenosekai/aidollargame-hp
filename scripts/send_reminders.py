#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
毎朝のリマインドメールを送るスクリプト。

- content/reminders.txt を読み、「今日が対象の予定」を拾う
- 直近7日のAI社員（自動記事生成）の作業報告をまとめる
- 上記をメール本文にして、SMTPで送信する

メール設定（GitHub の Secrets）が未登録の場合は、
本文をログに出すだけで何もせず正常終了する（CIを落とさない）。

依存ライブラリなし（Python標準ライブラリのみ）。
"""

import os
import re
import ssl
import smtplib
import subprocess
from email.message import EmailMessage
from email.utils import formataddr
from datetime import datetime, timedelta
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    JST = ZoneInfo("Asia/Tokyo")
except Exception:  # 念のためのフォールバック
    JST = None

REPO_ROOT = Path(__file__).resolve().parent.parent
REMINDERS_FILE = REPO_ROOT / "content" / "reminders.txt"

WEEKDAYS = {"月": 0, "火": 1, "水": 2, "木": 3, "金": 4, "土": 5, "日": 6}
WEEKDAY_JP = ["月", "火", "水", "木", "金", "土", "日"]


def now_jst():
    return datetime.now(JST) if JST else datetime.now()


def time_of_day(now):
    """JSTの時刻から朝/夜を判定（正午より前なら朝）。"""
    return "morning" if now.hour < 12 else "evening"


# ---------------------------------------------------------------------------
# リマインド一覧の読み込み・判定
# ---------------------------------------------------------------------------
def parse_reminders(text):
    """各行を (種別, パラメータ, 用件) に変換して返す。"""
    items = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "|" not in line:
            continue
        spec, msg = line.split("|", 1)
        spec, msg = spec.strip(), msg.strip()
        if not spec or not msg:
            continue

        # 2026-06-30 形式（その日だけ）
        m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", spec)
        if m:
            y, mo, d = (int(x) for x in m.groups())
            items.append(("once", (y, mo, d), msg))
            continue

        # 06-30 / 06/30 形式（毎年）
        m = re.fullmatch(r"(\d{1,2})[-/](\d{1,2})", spec)
        if m:
            mo, d = (int(x) for x in m.groups())
            items.append(("yearly", (mo, d), msg))
            continue

        # 毎日
        if spec.startswith("毎日"):
            items.append(("daily", None, msg))
            continue

        # 毎週 月
        if spec.startswith("毎週"):
            rest = spec[2:].strip()
            wd = WEEKDAYS.get(rest[:1]) if rest else None
            if wd is not None:
                items.append(("weekly", wd, msg))
            continue

        # 毎月 25
        if spec.startswith("毎月"):
            rest = spec[2:].strip()
            m = re.search(r"\d{1,2}", rest)
            if m:
                items.append(("monthly", int(m.group()), msg))
            continue

        # 解釈できない行は無視
    return items


def last_day_of_month(year, month):
    if month == 12:
        nxt = datetime(year + 1, 1, 1)
    else:
        nxt = datetime(year, month + 1, 1)
    return (nxt - timedelta(days=1)).day


def is_due_on(kind, param, target):
    """target（date）にこの予定が該当するか。"""
    if kind == "once":
        y, mo, d = param
        return (target.year, target.month, target.day) == (y, mo, d)
    if kind == "yearly":
        mo, d = param
        return (target.month, target.day) == (mo, d)
    if kind == "daily":
        return True
    if kind == "weekly":
        return target.weekday() == param
    if kind == "monthly":
        day = param
        # 月末を超える指定（毎月31など）は、その月の末日に寄せる
        clamped = min(day, last_day_of_month(target.year, target.month))
        return target.day == clamped
    return False


def collect_due(items, today):
    """今日ぶん＋3日以内に来る固定予定（早めのお知らせ）を返す。"""
    due_today = [msg for kind, p, msg in items if is_due_on(kind, p, today)]

    upcoming = []
    for offset in (1, 2, 3):
        d = today + timedelta(days=offset)
        for kind, p, msg in items:
            # 早めのお知らせは「日付が決まっているもの」だけ（毎日/毎週/毎月は除く）
            if kind in ("once", "yearly") and is_due_on(kind, p, d):
                label = f"{d.month}/{d.day}({WEEKDAY_JP[d.weekday()]})"
                upcoming.append((offset, label, msg))
    upcoming.sort(key=lambda x: x[0])
    return due_today, upcoming


# ---------------------------------------------------------------------------
# AI社員（自動記事生成）の作業報告
# ---------------------------------------------------------------------------
def ai_work_report():
    """直近7日の自動コミットを git log から拾って要約する。"""
    try:
        out = subprocess.run(
            ["git", "log", "--since=7 days ago", "--pretty=format:%s"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        ).stdout
    except Exception:
        return ["（作業履歴を取得できませんでした）"]

    lines = [l.strip() for l in out.splitlines() if l.strip()]
    auto = [l for l in lines if l.startswith("自動更新") or l.startswith("note:")]
    if not auto:
        return ["直近7日、自動生成された記事はありませんでした。"]
    # 重複を消して最大5件
    seen, report = set(), []
    for l in auto:
        if l in seen:
            continue
        seen.add(l)
        report.append("・" + l)
        if len(report) >= 5:
            break
    return report


# ---------------------------------------------------------------------------
# メール本文の組み立て
# ---------------------------------------------------------------------------
def build_body(today, mode, due_today, upcoming, due_tomorrow, work):
    wd = WEEKDAY_JP[today.weekday()]
    lines = []

    if mode == "evening":
        lines.append(f"おつかれさまです。{today.month}/{today.day}({wd}) の締めくくりです。")
        lines.append("")

        lines.append("■ 今日やること（おさらい）")
        if due_today:
            lines += ["・" + m for m in due_today]
        else:
            lines.append("・（今日の予定はありませんでした）")
        lines.append("")

        tomorrow = today + timedelta(days=1)
        twd = WEEKDAY_JP[tomorrow.weekday()]
        lines.append(f"■ 明日（{tomorrow.month}/{tomorrow.day}({twd})）の予定")
        if due_tomorrow:
            lines += ["・" + m for m in due_tomorrow]
        else:
            lines.append("・（登録された予定はありません）")
        lines.append("")
    else:
        lines.append(f"おはようございます。{today.month}/{today.day}({wd}) のリマインドです。")
        lines.append("")

        lines.append("■ 今日やること")
        if due_today:
            lines += ["・" + m for m in due_today]
        else:
            lines.append("・（登録された予定はありません）")
        lines.append("")

        if upcoming:
            lines.append("■ もうすぐ（3日以内）")
            lines += [f"・{label}  {msg}" for _, label, msg in upcoming]
            lines.append("")

    lines.append("■ AI社員の作業報告（直近7日）")
    lines += work
    lines.append("")

    lines.append("―――")
    lines.append("予定の追加・変更は content/reminders.txt を編集するだけでOKです。")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 送信
# ---------------------------------------------------------------------------
def send_email(subject, body):
    # 未設定のSecretは空文字で渡ってくるため、空なら既定値に倒す
    host = os.environ.get("SMTP_HOST") or "smtp.gmail.com"
    port = int(os.environ.get("SMTP_PORT") or "587")
    user = os.environ.get("SMTP_USER") or ""
    password = os.environ.get("SMTP_PASS") or ""
    mail_to = os.environ.get("MAIL_TO") or "nosuke@aidollargame.com"
    mail_from = os.environ.get("MAIL_FROM") or user

    if not user or not password:
        print("=== メール設定（SMTP_USER / SMTP_PASS）が未登録のため送信スキップ ===")
        print(f"(設定後はこの本文が {mail_to} に届きます)\n")
        print(f"Subject: {subject}\n")
        print(body)
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr(("AI社員", mail_from))
    msg["To"] = mail_to
    msg.set_content(body)

    context = ssl.create_default_context()
    with smtplib.SMTP(host, port, timeout=30) as server:
        server.starttls(context=context)
        server.login(user, password)
        server.send_message(msg)
    print(f"リマインドメールを送信しました → {mail_to}")


def main():
    now = now_jst()
    today = now.date()
    mode = os.environ.get("REMIND_MODE") or time_of_day(now)

    items = []
    if REMINDERS_FILE.exists():
        items = parse_reminders(REMINDERS_FILE.read_text(encoding="utf-8"))
    else:
        print(f"{REMINDERS_FILE} が見つかりません。予定なしで続行します。")

    due_today, upcoming = collect_due(items, today)
    due_tomorrow = [msg for kind, p, msg in items
                    if is_due_on(kind, p, today + timedelta(days=1))]
    work = ai_work_report()

    body = build_body(today, mode, due_today, upcoming, due_tomorrow, work)
    wd = WEEKDAY_JP[today.weekday()]
    label = "夜" if mode == "evening" else "朝"
    subject = f"【AI社員より】{today.month}/{today.day}({wd}) のリマインド（{label}）"

    send_email(subject, body)


if __name__ == "__main__":
    main()
