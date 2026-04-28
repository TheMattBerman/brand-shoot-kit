"""Curl-based scout adapter. Extracted from scripts/scout-url.sh."""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any


def _first(pattern: str, text: str) -> str:
    m = re.search(pattern, text, flags=re.I | re.S)
    return unescape(m.group(1).strip()) if m else ""


def _try_json(value: str) -> Any:
    try:
        return json.loads(value)
    except Exception:
        return None


def _fetch_html(url: str) -> str:
    """Fetch HTML via curl. file:// URLs are handled directly for fixture testing."""
    if url.startswith("file://"):
        return Path(url[len("file://"):]).read_text(encoding="utf-8", errors="ignore")
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        subprocess.run(
            ["curl", "-L", "--max-time", "20", "-A", "brand-shoot-kit/0.1", url, "-o", tmp_path],
            check=True,
            capture_output=True,
        )
        return Path(tmp_path).read_text(encoding="utf-8", errors="ignore")
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def scrape(url: str, *, fixture_dir: Path | None = None) -> dict:
    """Run the curl-based scout against url. Returns the normalized scout payload."""
    # fixture_dir is accepted for adapter-contract uniformity; curl adapter ignores it.
    html = _fetch_html(url)

    title = _first(r"<title[^>]*>(.*?)</title>", html)
    meta_desc = _first(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', html)
    og_title = _first(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']', html)
    og_desc = _first(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](.*?)["\']', html)

    h1s_raw = re.findall(r"<h1[^>]*>(.*?)</h1>", html, flags=re.I | re.S)
    h1s = [re.sub(r"<[^>]+>", " ", unescape(x)).strip() for x in h1s_raw]
    h1s = [x for x in h1s if x][:5]

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

    seen: set[str] = set()
    uniq: list[str] = []
    for i in clean_imgs:
        if i not in seen:
            uniq.append(i)
            seen.add(i)

    json_ld: list[Any] = []
    for raw in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, flags=re.I | re.S):
        text = unescape(raw).strip()
        if not text:
            continue
        parsed = _try_json(text)
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
        blob = re.sub(r';\s*$', '', m.group(1).strip())
        parsed = _try_json(blob)
        if isinstance(parsed, dict):
            shopify_product = parsed.get("product") if isinstance(parsed.get("product"), dict) else parsed
            break

    metafields = None
    for pat in [
        r'"metafields"\s*:\s*(\{.*?\})\s*(?:,|\})',
        r'window\.meta\s*=\s*(\{.*?\});',
    ]:
        m = re.search(pat, html, flags=re.I | re.S)
        if not m:
            continue
        parsed = _try_json(m.group(1).strip())
        if isinstance(parsed, dict):
            metafields = parsed
            break

    return {
        "url": url,
        "title": title,
        "meta_description": meta_desc,
        "og_title": og_title,
        "og_description": og_desc,
        "h1": h1s,
        "image_urls": uniq[:40],
        "json_ld": json_ld[:8],
        "shopify_product_json": shopify_product,
        "metafields": metafields,
        "degraded_mode": True,
        "scraper": "curl",
        "note": "Basic HTML extraction + embedded JSON-LD/Shopify parse when available. If FIRECRAWL_API_KEY is configured, Firecrawl is the default scraper.",
        "scrape_provenance": {
            "scraper": "curl",
            "scraper_version": "shim-1",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "request_url": url,
            "fixture_used": None,
            "forced_by": None,
        },
    }
