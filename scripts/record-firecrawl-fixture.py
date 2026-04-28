#!/usr/bin/env python3
"""Record a real Firecrawl /v2/scrape response into evals/fixtures/firecrawl/<sha>.json.

Usage:
  FIRECRAWL_API_KEY=... ./scripts/record-firecrawl-fixture.py --url <URL>

This is the only path that hits Firecrawl during testing.
./evals/run.py never invokes this script.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from adapters.firecrawl_scrape import _build_request_body, FIRECRAWL_API, FIRECRAWL_ENDPOINT  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a Firecrawl scrape response as a fixture.")
    parser.add_argument("--url", required=True, help="The product URL to scrape.")
    parser.add_argument(
        "--out-dir",
        default=str(ROOT / "evals" / "fixtures" / "firecrawl"),
        help="Where to write the fixture (default: evals/fixtures/firecrawl).",
    )
    args = parser.parse_args()

    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        sys.stderr.write("error: FIRECRAWL_API_KEY is required to record a fixture\n")
        return 1

    body = json.dumps(_build_request_body(args.url)).encode("utf-8")
    req = urllib.request.Request(
        f"{FIRECRAWL_API}{FIRECRAWL_ENDPOINT}",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "brand-shoot-kit/firecrawl-fixture-recorder",
        },
    )
    started = time.monotonic()
    with urllib.request.urlopen(req, timeout=60) as resp:
        response = json.loads(resp.read().decode("utf-8"))
    elapsed_ms = int((time.monotonic() - started) * 1000)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(args.url.encode("utf-8")).hexdigest()
    out_path = out_dir / f"{sha}.json"

    fixture = {
        "request": {
            "url": args.url,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "firecrawl_endpoint": FIRECRAWL_ENDPOINT,
            "response_ms": elapsed_ms,
        },
        "response": response,
    }
    out_path.write_text(json.dumps(fixture, indent=2), encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
