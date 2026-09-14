#!/bin/bash
# 変更したページを IndexNow に通知する。
#
#   ./indexnow-ping.sh articles/about-aidollargame.html llms.txt
#   ./indexnow-ping.sh --sitemap-recent 20   # sitemap.xml の lastmod が新しい順に20件
#
# 通知先は Bing / Yandex / Seznam / Naver など IndexNow 参加エンジン。
# Google は IndexNow に参加していないので、Google の再クロールは早まらない。
# Google 側を急がせたい場合は Search Console の URL 検査から手動で申請する。
set -euo pipefail

HOST="aidollargame.com"
KEY="985f63c466d486c4b96de528c3b3e2ad"

cd "$(dirname "$0")"

if [ "${1:-}" = "--sitemap-recent" ]; then
  n="${2:-20}"
  urls=$(python3 - "$n" <<'PY'
import re, sys, xml.etree.ElementTree as ET
n = int(sys.argv[1])
ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
root = ET.parse("sitemap.xml").getroot()
rows = []
for u in root.findall("s:url", ns):
    loc = u.findtext("s:loc", default="", namespaces=ns)
    mod = u.findtext("s:lastmod", default="", namespaces=ns)
    if loc:
        rows.append((mod, loc))
rows.sort(reverse=True)
for _, loc in rows[:n]:
    print(loc)
PY
)
elif [ $# -gt 0 ]; then
  urls=""
  for p in "$@"; do
    p="${p#/}"
    [ -f "$p" ] || { echo "そんなファイルはない: $p" >&2; exit 1; }
    urls="${urls}https://${HOST}/${p}"$'\n'
  done
else
  echo "使い方: $0 <変更したファイル> [...]  /  $0 --sitemap-recent [件数]" >&2
  exit 1
fi

urls=$(echo "$urls" | sed '/^$/d')
[ -n "$urls" ] || { echo "送るURLがない" >&2; exit 1; }

echo "送信するURL:"
echo "$urls" | sed 's/^/  /'

payload=$(python3 - "$HOST" "$KEY" <<PY
import json, sys
host, key = sys.argv[1], sys.argv[2]
urls = """$urls""".split()
print(json.dumps({
    "host": host,
    "key": key,
    "keyLocation": f"https://{host}/{key}.txt",
    "urlList": urls,
}, ensure_ascii=False))
PY
)

code=$(curl -sS -o /tmp/indexnow-resp.txt -w "%{http_code}" -X POST "https://api.indexnow.org/indexnow" \
  -H "Content-Type: application/json; charset=utf-8" --max-time 30 -d "$payload")

echo ""
echo "HTTPステータス: $code"
[ -s /tmp/indexnow-resp.txt ] && cat /tmp/indexnow-resp.txt
case "$code" in
  200|202) echo "受理された。" ;;
  *) echo "受理されていない。キーの公開状態を確認: https://${HOST}/${KEY}.txt" >&2; exit 1 ;;
esac
