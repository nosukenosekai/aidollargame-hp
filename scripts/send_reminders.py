#!/usr/bin/env python3
"""今日(JST)が指定日のリマインドをメール送信する。

content/reminders.txt を読み、当日分の本文をまとめて1通のメールにして送る。
GitHub Actions から朝・夜の2回実行される想定。

必要な環境変数(リポジトリ Secrets で設定):
  GMAIL_USER          送信元 Gmail アドレス（受信先も同じ）
  GMAIL_APP_PASSWORD  Gmail アプリパスワード（16桁）
任意:
  REMINDER_TO         送信先を変えたい場合に指定（未指定なら GMAIL_USER）
  REMINDER_SLOT       "朝" / "夜"（メール件名の表示用。未指定なら時刻から自動判定）
"""

import os
import smtplib
import sys
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.utils import formatdate
from pathlib import Path

JST = timezone(timedelta(hours=9))
REMINDERS_FILE = Path(__file__).resolve().parent.parent / "content" / "reminders.txt"


def load_due_reminders(today_str):
    """当日(today_str=YYYY-MM-DD)のリマインド本文を一覧で返す。"""
    if not REMINDERS_FILE.exists():
        return []
    due = []
    for raw in REMINDERS_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "|" not in line:
            continue
        date_part, body = line.split("|", 1)
        if date_part.strip() == today_str:
            due.append(body.strip())
    return due


def build_message(due, now, slot):
    weekday = "月火水木金土日"[now.weekday()]
    date_label = f"{now.month}/{now.day}({weekday})"
    lines = [f"おはようございます。{date_label} のリマインドです。" if slot == "朝"
             else f"お疲れさまです。{date_label} のリマインドです。", ""]
    lines.append("■ 今日やること")
    for body in due:
        lines.append(f"・{body}")
    lines += ["", "―――", "予定の追加・変更は content/reminders.txt を編集するだけでOKです。"]
    return "\n".join(lines), f"【リマインド】{date_label}（{slot}）"


def main():
    user = os.environ.get("GMAIL_USER")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not password:
        print("ERROR: GMAIL_USER / GMAIL_APP_PASSWORD が未設定です。", file=sys.stderr)
        return 1

    to_addr = os.environ.get("REMINDER_TO", user)
    now = datetime.now(JST)
    slot = os.environ.get("REMINDER_SLOT") or ("朝" if now.hour < 14 else "夜")
    today_str = now.strftime("%Y-%m-%d")

    due = load_due_reminders(today_str)
    if not due:
        print(f"{today_str}: 配信対象のリマインドはありません。送信スキップ。")
        return 0

    body, subject = build_message(due, now, slot)
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_addr
    msg["Date"] = formatdate(localtime=True)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(user, password)
        server.sendmail(user, [to_addr], msg.as_string())

    print(f"{today_str}: {len(due)}件のリマインドを {to_addr} に送信しました。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
