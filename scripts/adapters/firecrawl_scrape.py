"""Firecrawl /v2/scrape adapter.

Live HTTP path (Task 4) and fixture-replay path (this task) share a single
_normalize() function so the adapter contract is identical regardless
of where the response came from.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

FIRECRAWL_ENDPOINT = "/v2/scrape"
FIRECRAWL_API = "https://api.firecrawl.dev"

_PRODUCT_SCHEMA = {
    "type": "object",
    "properties": {
        "brand":                 {"type": "string"},
        "product_name":          {"type": "string"},
        "category_hint":         {"type": "string", "description": "e.g. coffee, skincare, supplement, cleaning_kit"},
        "price":                 {"type": "string"},
        "variants":              {"type": "array", "items": {"type": "string"}},
        "ingredients":           {"type": "array", "items": {"type": "string"}},
        "claims":                {"type": "array", "items": {"type": "string"}},
        "packaging_description": {"type": "string"},
        "main_image_url":        {"type": "string", "description": "The single primary product hero image"},
        "product_image_urls":    {"type": "array", "items": {"type": "string"},
                                   "description": "Real product photos only — no logos, badges, review widgets, nutrition panels, cross-sells"},
    },
}

_DEFAULT_EXCLUDE_TAGS = [
    "nav", "footer", "header",
    "[role=banner]", "[role=contentinfo]",
    ".announcement", ".reviews", ".cross-sell", ".related-products",
]


def _build_request_body(url: str) -> dict:
    return {
        "url": url,
        "formats": [
            "html",
            "links",
            {
                "type": "json",
                "prompt": "Extract the product as listed on this page. Use only what's literally visible on the PDP.",
                "schema": _PRODUCT_SCHEMA,
            },
        ],
        "onlyMainContent": True,
        "excludeTags": _DEFAULT_EXCLUDE_TAGS,
        "waitFor": 1500,
        "timeout": 25000,
    }


def _post(url: str, *, api_key: str, timeout_s: float = 30.0) -> tuple[dict, int]:
    if any(ch in api_key for ch in "\r\n\t\x00"):
        raise FirecrawlScrapeError(
            "missing_api_key",
            "FIRECRAWL_API_KEY contains control characters; refusing to send.",
        )
    body = json.dumps(_build_request_body(url)).encode("utf-8")
    req = urllib.request.Request(
        f"{FIRECRAWL_API}{FIRECRAWL_ENDPOINT}",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "brand-shoot-kit/firecrawl-adapter",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read()
            status = resp.status
        try:
            payload = json.loads(raw.decode("utf-8"))
        except UnicodeDecodeError as e:
            raise FirecrawlScrapeError(
                "response_invalid",
                f"Firecrawl response was not UTF-8: {e}",
                http_status=status,
            ) from e
        except json.JSONDecodeError as e:
            preview = raw[:200].decode("utf-8", errors="replace")
            raise FirecrawlScrapeError(
                "response_invalid",
                f"Firecrawl response was not valid JSON: {e}. First 200 bytes: {preview!r}",
                http_status=status,
            ) from e
        return payload, status
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8", errors="ignore")
        except Exception:
            detail = ""
        raise FirecrawlScrapeError("api_error", detail or e.reason or str(e), http_status=e.code) from e
    except urllib.error.URLError as e:
        raise FirecrawlScrapeError("network_error", str(e.reason)) from e
    except TimeoutError as e:
        raise FirecrawlScrapeError("timeout", str(e)) from e


def _format_fixture_path(fixture_path: Path) -> str:
    """Return a CWD-relative path string when possible, absolute otherwise.

    Path.relative_to raises ValueError if the fixture isn't under cwd or if
    one side is relative — fall back to the absolute path so we never crash
    just to record provenance.
    """
    try:
        return str(fixture_path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(fixture_path.resolve())


class FirecrawlScrapeError(Exception):
    """Raised on any non-recoverable Firecrawl scrape failure."""

    def __init__(self, kind: str, detail: str, http_status: int | None = None):
        super().__init__(f"{kind}: {detail}")
        self.kind = kind
        self.detail = detail
        self.http_status = http_status


def _fixture_path(fixture_dir: Path, url: str) -> Path:
    sha = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return fixture_dir / f"{sha}.json"


def _load_fixture(fixture_dir: Path, url: str) -> tuple[dict, Path]:
    path = _fixture_path(fixture_dir, url)
    if not path.exists():
        raise FirecrawlScrapeError(
            "fixture_missing",
            f"No Firecrawl fixture for {url} at {path}. "
            f"Record one with: ./scripts/record-firecrawl-fixture.py --url '{url}'",
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    response = raw.get("response") or {}
    if not response.get("success"):
        raise FirecrawlScrapeError("fixture_invalid", f"Fixture at {path} has success=false")
    data = response.get("data")
    if not isinstance(data, dict):
        raise FirecrawlScrapeError("fixture_invalid", f"Fixture at {path} missing data object")
    return data, path


def _normalize(url: str, data: dict, *, fixture_path: Path | None = None,
               firecrawl_meta: dict | None = None, forced_by: str | None = None) -> dict:
    """Convert a Firecrawl /v2/scrape response into the adapter's canonical payload."""
    metadata = data.get("metadata") or {}
    json_extract = data.get("json") or {}

    # Image inventory: prefer schema-extracted product images; fall back to schema main_image_url.
    product_imgs = list(json_extract.get("product_image_urls") or [])
    main_img = json_extract.get("main_image_url") or ""
    if main_img and main_img not in product_imgs:
        product_imgs = [main_img] + product_imgs

    return {
        "url": url,
        "title": metadata.get("title", "") or "",
        "meta_description": metadata.get("description", "") or "",
        "og_title": metadata.get("ogTitle", "") or metadata.get("title", ""),
        "og_description": metadata.get("ogDescription", "") or metadata.get("description", ""),
        "h1": [],  # Firecrawl doesn't separately surface h1s; leave to enrich_scout fallback if needed.
        "image_urls": product_imgs[:40],
        "json_ld": [],  # Firecrawl already extracted structured data via schema; json_ld stays empty.
        "shopify_product_json": None,
        "metafields": None,
        "degraded_mode": False,
        "scraper": "firecrawl",
        "note": "Firecrawl /v2/scrape with JSON schema extraction.",
        "rendered_html": data.get("html", "") or "",
        "structured_product": json_extract or {},
        "main_image_url": main_img or None,
        "excluded_image_urls": [],  # populated when excludeTags filtering surfaces in v2 (future).
        "firecrawl_meta": firecrawl_meta or {},
        "scrape_provenance": {
            "scraper": "firecrawl",
            "scraper_version": "v2",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "request_url": url,
            "fixture_used": _format_fixture_path(fixture_path) if fixture_path else None,
            "forced_by": forced_by,
            "firecrawl_meta": firecrawl_meta or {"endpoint": FIRECRAWL_ENDPOINT},
        },
    }


def scrape(url: str, *, fixture_dir: Path | None = None) -> dict:
    """Scrape url. If BSK_FIRECRAWL_FIXTURE_DIR (or fixture_dir arg) is set, replay from disk."""
    fixture_dir = fixture_dir or (Path(os.environ["BSK_FIRECRAWL_FIXTURE_DIR"])
                                  if os.environ.get("BSK_FIRECRAWL_FIXTURE_DIR") else None)

    if fixture_dir:
        data, path = _load_fixture(fixture_dir, url)
        firecrawl_meta = {
            "endpoint": FIRECRAWL_ENDPOINT,
            "request_id": "fixture",
            "credits_used": 0,
            "response_ms": 0,
        }
        return _normalize(url, data, fixture_path=path, firecrawl_meta=firecrawl_meta)

    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        raise FirecrawlScrapeError(
            "missing_api_key",
            "FIRECRAWL_API_KEY is not set. Either set it, pass --scraper curl, or "
            "provide a fixture_dir for replay testing.",
        )

    started = time.monotonic()
    payload, status = _post(url, api_key=api_key)
    elapsed_ms = int((time.monotonic() - started) * 1000)

    if not isinstance(payload, dict) or not payload.get("success"):
        detail = payload.get("error") if isinstance(payload, dict) else "non-dict response"
        raise FirecrawlScrapeError("api_unsuccessful", str(detail), http_status=status)

    data = payload.get("data")
    if not isinstance(data, dict) or not data.get("metadata"):
        raise FirecrawlScrapeError("empty_response", "Firecrawl returned 200 OK but data was empty.", http_status=status)

    firecrawl_meta = {
        "endpoint": FIRECRAWL_ENDPOINT,
        "request_id": payload.get("scrapeId") or payload.get("id") or "",
        "credits_used": payload.get("creditsUsed", 0),
        "response_ms": elapsed_ms,
    }
    return _normalize(url, data, fixture_path=None, firecrawl_meta=firecrawl_meta)
