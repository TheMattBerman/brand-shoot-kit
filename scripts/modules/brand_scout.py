#!/usr/bin/env python3
"""Module entrypoint: brand-scout -> scout.json.

Dispatches to scripts/adapters/{curl_scrape, firecrawl_scrape} based on:
  1. --scraper {auto,curl,firecrawl}
  2. BSK_FORCE_SCRAPER env var
  3. FIRECRAWL_API_KEY env var (present -> firecrawl)
  4. default -> curl
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from packet_utils import dump_json, load_json  # noqa: E402
from scout_structured import enrich_scout  # noqa: E402

from adapters import curl_scrape  # noqa: E402
from adapters import firecrawl_scrape  # noqa: E402
from adapters.firecrawl_scrape import FirecrawlScrapeError  # noqa: E402

VALID_SCRAPERS = ("auto", "curl", "firecrawl")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run brand-scout module and write scout.json")
    p.add_argument("--url", help="Product URL to scout")
    p.add_argument("--scout-json", help="Base scout JSON to enrich (skips scraping)")
    p.add_argument("--packet", help="Packet directory (writes <packet>/scout.json)")
    p.add_argument("--out", help="Output scout.json path")
    p.add_argument("--scraper", choices=VALID_SCRAPERS, default="auto",
                   help="Scraper selection. 'auto' follows env precedence; 'curl' or 'firecrawl' forces.")
    return p.parse_args()


def resolve_out(args: argparse.Namespace) -> Path:
    if args.out:
        return Path(args.out).resolve()
    if args.packet:
        return Path(args.packet).resolve() / "scout.json"
    raise SystemExit("error: provide --out or --packet")


def pick_scraper(flag: str) -> tuple[str, str | None]:
    """Return (scraper_name, forced_by_label_or_None)."""
    if flag in ("curl", "firecrawl"):
        return flag, "--scraper"
    forced_env = os.environ.get("BSK_FORCE_SCRAPER")
    if forced_env in ("curl", "firecrawl"):
        return forced_env, "BSK_FORCE_SCRAPER"
    if os.environ.get("FIRECRAWL_API_KEY"):
        return "firecrawl", None
    return "curl", None


def print_failure(url: str, e: FirecrawlScrapeError) -> None:
    sys.stderr.write(
        "\n────────────────────────────────────────────────────\n"
        f"Firecrawl scrape failed: {e.kind}\n"
        f"{e.detail}\n"
        f"URL:    {url}\n"
        f"Status: {e.http_status if e.http_status is not None else 'n/a'}\n"
        "\n"
        "Recovery:\n"
        "  Re-run with --scraper curl to use the curl fallback.\n"
        "  Example:\n"
        f"    {Path(sys.argv[0]).name} --url \"{url}\" --scraper curl …\n"
        "\n"
        "Or unset FIRECRAWL_API_KEY to default to curl.\n"
        "────────────────────────────────────────────────────\n"
    )


def run_scrape(url: str, scraper: str, forced_by: str | None) -> dict:
    if scraper == "firecrawl":
        payload = firecrawl_scrape.scrape(url)
    else:
        payload = curl_scrape.scrape(url)
    # Stamp forced_by on provenance if dispatcher selected it.
    prov = payload.setdefault("scrape_provenance", {})
    if forced_by and not prov.get("forced_by"):
        prov["forced_by"] = forced_by
    return payload


def print_banner(scraper: str, url: str, payload: dict | None = None) -> None:
    if scraper == "firecrawl":
        meta = (payload or {}).get("firecrawl_meta") or {}
        endpoint = meta.get("endpoint", "/v2/scrape")
        sys.stderr.write(f"[scout] scraper=firecrawl  endpoint={endpoint}  est_credits=~1  url={url}\n")
    else:
        sys.stderr.write(f"[scout] scraper=curl  url={url}\n")


def main() -> int:
    args = parse_args()
    out = resolve_out(args)
    out.parent.mkdir(parents=True, exist_ok=True)

    if args.scout_json:
        base = load_json(Path(args.scout_json).resolve())
    elif args.url:
        scraper, forced_by = pick_scraper(args.scraper)
        print_banner(scraper, args.url)
        try:
            base = run_scrape(args.url, scraper, forced_by)
        except FirecrawlScrapeError as e:
            print_failure(args.url, e)
            return 2
    else:
        raise SystemExit("error: provide --url or --scout-json")

    dump_json(out, enrich_scout(base))
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
