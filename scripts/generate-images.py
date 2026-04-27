#!/usr/bin/env python3
"""Generate Brand Shoot images from packet prompts.

Default behavior is dry-run to avoid API spend. Use `--live` with OPENAI_API_KEY
for provider-backed generation.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List

from packet_utils import dump_json, ensure_packet_dir, parse_generation_prompts, read_brand_product, slug

TINY_PLACEHOLDER_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAJq4QW0AAAAASUVORK5CYII="
)


class OpenAIImageProvider:
    def __init__(self, api_key: str, model: str, size: str) -> None:
        self.api_key = api_key
        self.model = model
        self.size = size

    def generate(self, prompt: str) -> bytes:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "size": self.size,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            "https://api.openai.com/v1/images/generations",
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI image generation failed ({exc.code}): {details}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"OpenAI request failed: {exc}") from exc

        items = body.get("data") or []
        if not items:
            raise RuntimeError(f"OpenAI response missing data: {body}")
        first = items[0]
        b64 = first.get("b64_json")
        if b64:
            return base64.b64decode(b64)

        image_url = first.get("url")
        if image_url:
            try:
                with urllib.request.urlopen(image_url, timeout=120) as image_resp:
                    return image_resp.read()
            except urllib.error.URLError as exc:
                raise RuntimeError(f"OpenAI image URL download failed: {exc}") from exc

        raise RuntimeError(f"OpenAI response missing b64_json/url: {body}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate images from a Brand Shoot packet")
    p.add_argument("--packet", help="Path to packet directory")
    p.add_argument("--prompts", help="Path to 04-generation-prompts.md")
    p.add_argument("--out", help="Generated assets directory (default: <packet>/assets/generated)")
    p.add_argument("--manifest", help="Generation manifest path (default: <out>/generation-manifest.json)")
    p.add_argument("--live", action="store_true", help="Call OpenAI Images API (requires OPENAI_API_KEY)")
    p.add_argument("--model", default="gpt-image-2", help="OpenAI image model (live mode)")
    p.add_argument("--size", default="1024x1024", help="Image size sent to provider in live mode")
    p.add_argument("--limit", type=int, default=0, help="Optional shot limit for quick runs")
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing image files")
    p.add_argument("--asset-ids", default="", help="Comma-separated asset IDs to generate (default: all)")
    p.add_argument("--prompt-overrides", help="JSON map of asset_id -> prompt override")
    return p.parse_args()


def resolve_paths(args: argparse.Namespace) -> Dict[str, Path]:
    if not args.packet and not args.prompts:
        raise SystemExit("error: provide --packet or --prompts")

    packet_dir = Path(args.packet).resolve() if args.packet else None
    prompts_path = Path(args.prompts).resolve() if args.prompts else None

    if packet_dir:
        ensure_packet_dir(packet_dir)
        if not prompts_path:
            prompts_path = packet_dir / "04-generation-prompts.md"

    if not prompts_path or not prompts_path.exists():
        raise SystemExit(f"error: prompts not found: {prompts_path}")

    if packet_dir is None:
        packet_dir = prompts_path.parent

    out_dir = Path(args.out).resolve() if args.out else packet_dir / "assets" / "generated"
    manifest_path = Path(args.manifest).resolve() if args.manifest else out_dir / "generation-manifest.json"

    return {
        "packet_dir": packet_dir,
        "prompts_path": prompts_path,
        "out_dir": out_dir,
        "manifest_path": manifest_path,
    }


def write_placeholder(path: Path, shot: Dict[str, Any]) -> None:
    path.write_bytes(TINY_PLACEHOLDER_PNG)
    sidecar = path.with_suffix(".placeholder.txt")
    sidecar.write_text(
        "\n".join(
            [
                "dry_run_placeholder=true",
                f"asset_id={shot['asset_id']}",
                f"shot_name={shot['shot_name']}",
                f"ratio={shot['ratio']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def deterministic_file_name(shot: Dict[str, Any]) -> str:
    ratio_slug = shot.get("ratio", "unknown").replace(":", "x")
    return f"{shot['asset_id']}--{slug(shot['shot_name'])}--{ratio_slug}.png"


def parse_asset_filter(raw: str) -> set[str]:
    return {x.strip() for x in raw.split(",") if x.strip()} if raw else set()


def load_prompt_overrides(path: str | None) -> Dict[str, str]:
    if not path:
        return {}
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("error: --prompt-overrides must be a JSON object")
    return {str(k): str(v) for k, v in payload.items()}


def main() -> int:
    args = parse_args()
    paths = resolve_paths(args)

    packet_dir = paths["packet_dir"]
    prompts_path = paths["prompts_path"]
    out_dir = paths["out_dir"]
    manifest_path = paths["manifest_path"]

    out_dir.mkdir(parents=True, exist_ok=True)

    shots = parse_generation_prompts(prompts_path)
    if not shots:
        print(f"error: no shots parsed from {prompts_path}", file=sys.stderr)
        return 2

    asset_filter = parse_asset_filter(args.asset_ids)
    if asset_filter:
        shots = [s for s in shots if str(s.get("asset_id")) in asset_filter]

    if args.limit and args.limit > 0:
        shots = shots[: args.limit]

    if not shots:
        print("error: no matching shots to generate", file=sys.stderr)
        return 2

    prompt_overrides = load_prompt_overrides(args.prompt_overrides)
    for shot in shots:
        asset_id = str(shot.get("asset_id"))
        if asset_id in prompt_overrides:
            shot["prompt"] = prompt_overrides[asset_id]
            shot["prompt_override_applied"] = True

    brand_product = read_brand_product(packet_dir / "00-brand-analysis.md")

    provider = None
    mode = "dry-run"
    if args.live:
        if not os.environ.get("OPENAI_API_KEY"):
            print("error: --live set but OPENAI_API_KEY is not available", file=sys.stderr)
            return 2
        provider = OpenAIImageProvider(os.environ["OPENAI_API_KEY"], args.model, args.size)
        mode = "live"

    run_stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    entries: List[Dict[str, Any]] = []

    for shot in shots:
        filename = deterministic_file_name(shot)
        image_path = out_dir / filename

        if image_path.exists() and not args.overwrite:
            entries.append(
                {
                    **shot,
                    "status": "skipped-existing",
                    "provider": mode,
                    "dry_run": mode != "live",
                    "image_path": str(image_path),
                }
            )
            continue

        entry = {
            **shot,
            "status": "generated",
            "provider": mode,
            "dry_run": mode != "live",
            "image_path": str(image_path),
        }

        if mode == "live" and provider is not None:
            try:
                png_bytes = provider.generate(shot["prompt"])
                image_path.write_bytes(png_bytes)
                entry["image_sha256"] = hashlib.sha256(png_bytes).hexdigest()
            except Exception as exc:  # pragma: no cover
                entry["status"] = "error"
                entry["error"] = str(exc)
        else:
            write_placeholder(image_path, shot)
            entry["image_sha256"] = hashlib.sha256(TINY_PLACEHOLDER_PNG).hexdigest()

        entries.append(entry)

    run_payload = {
        "run_id": f"gen-{run_stamp}",
        "timestamp_utc": run_stamp,
        "packet_dir": str(packet_dir),
        "prompts_path": str(prompts_path),
        "output_dir": str(out_dir),
        "provider": mode,
        "model": args.model if mode == "live" else "none",
        "size": args.size,
        "brand": brand_product["brand"],
        "product": brand_product["product"],
        "total_shots": len(shots),
        "entries": entries,
    }

    dump_json(manifest_path, run_payload)
    print(str(manifest_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
