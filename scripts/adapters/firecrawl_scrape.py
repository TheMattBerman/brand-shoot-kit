"""Firecrawl /v2/scrape adapter.

Live HTTP path (Task 4) and fixture-replay path (this task) share a single
_normalize() function so the adapter contract is identical regardless
of where the response came from.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

FIRECRAWL_ENDPOINT = "/v2/scrape"
FIRECRAWL_API = "https://api.firecrawl.dev"


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

    # Live path lives in Task 4. Until then, fixture mode is required.
    raise FirecrawlScrapeError(
        "not_implemented",
        "Live Firecrawl HTTP path is not yet implemented. "
        "Set BSK_FIRECRAWL_FIXTURE_DIR or pass fixture_dir to use fixture replay.",
    )
