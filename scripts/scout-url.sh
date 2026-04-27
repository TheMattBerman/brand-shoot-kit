#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage: $0 --url PRODUCT_URL [--out FILE]

Fetch lightweight product page context (title, description, image URLs) without heavy dependencies.
USAGE
}

URL=""
OUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --url) URL="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ -z "$URL" ]]; then
  echo "--url is required" >&2
  usage
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required for scout-url.sh" >&2
  exit 1
fi

TMP_HTML="$(mktemp)"
curl -L --max-time 20 -A "brand-shoot-kit/0.1" "$URL" -o "$TMP_HTML" >/dev/null

JSON_OUT=$(python3 - "$URL" "$TMP_HTML" <<'PY'
import json
import re
import sys
from html import unescape

url = sys.argv[1]
path = sys.argv[2]
html = open(path, "r", encoding="utf-8", errors="ignore").read()

def first(pattern, text):
    m = re.search(pattern, text, flags=re.I | re.S)
    return unescape(m.group(1).strip()) if m else ""

def try_json(value):
    try:
        return json.loads(value)
    except Exception:
        return None

title = first(r"<title[^>]*>(.*?)</title>", html)
meta_desc = first(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', html)
og_title = first(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']', html)
og_desc = first(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](.*?)["\']', html)

h1s = [unescape(x.strip()) for x in re.findall(r"<h1[^>]*>(.*?)</h1>", html, flags=re.I | re.S)]
h1s = [re.sub(r"<[^>]+>", " ", x).strip() for x in h1s if x.strip()]

imgs = re.findall(r'<img[^>]+src=["\'](.*?)["\']', html, flags=re.I | re.S)
imgs += re.findall(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](.*?)["\']', html, flags=re.I)

clean_imgs = []
for i in imgs:
    i = i.strip()
    if not i:
        continue
    if i.startswith("//"):
        i = "https:" + i
    clean_imgs.append(i)

seen = set()
uniq = []
for i in clean_imgs:
    if i not in seen:
        uniq.append(i)
        seen.add(i)

json_ld = []
for raw in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, flags=re.I | re.S):
    text = unescape(raw).strip()
    if not text:
        continue
    parsed = try_json(text)
    if parsed is not None:
        json_ld.append(parsed)

shopify_product = None
for pat in [
    r'var\s+meta\s*=\s*(\{.*?\});',
    r'window\.__PRELOADED_STATE__\s*=\s*(\{.*?\});',
    r'"product"\s*:\s*(\{.*?\})\s*,\s*"selectedVariant"',
    r'<script[^>]+id=["\']ProductJson-[^"\']+["\'][^>]*>(.*?)</script>',
]:
    m = re.search(pat, html, flags=re.I | re.S)
    if not m:
        continue
    blob = m.group(1).strip()
    blob = re.sub(r';\s*$', '', blob)
    parsed = try_json(blob)
    if isinstance(parsed, dict):
        if "product" in parsed and isinstance(parsed.get("product"), dict):
            shopify_product = parsed.get("product")
        else:
            shopify_product = parsed
        break

metafields = None
for pat in [
    r'"metafields"\s*:\s*(\{.*?\})\s*(?:,|\})',
    r'window\.meta\s*=\s*(\{.*?\});',
]:
    m = re.search(pat, html, flags=re.I | re.S)
    if not m:
        continue
    parsed = try_json(m.group(1).strip())
    if isinstance(parsed, dict):
        metafields = parsed
        break

payload = {
    "url": url,
    "title": title,
    "meta_description": meta_desc,
    "og_title": og_title,
    "og_description": og_desc,
    "h1": h1s[:5],
    "image_urls": uniq[:40],
    "json_ld": json_ld[:8],
    "shopify_product_json": shopify_product,
    "metafields": metafields,
    "degraded_mode": True,
    "note": "Basic HTML extraction + embedded JSON-LD/Shopify parse when available. If FIRECRAWL_API_KEY is configured, use richer extraction externally.",
}
print(json.dumps(payload, indent=2))
PY
)

if [[ -n "$OUT" ]]; then
  mkdir -p "$(dirname "$OUT")"
  printf '%s\n' "$JSON_OUT" > "$OUT"
  echo "$OUT"
else
  printf '%s\n' "$JSON_OUT"
fi

rm -f "$TMP_HTML"
