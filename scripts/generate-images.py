#!/usr/bin/env python3
"""Generate Brand Shoot images from packet prompts.

Default behavior is dry-run to avoid API spend. Use `--live` with OPENAI_API_KEY
for provider-backed generation.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import mimetypes
import os
import shutil
import struct
import sys
import urllib.error
import urllib.request
import zlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse
import uuid

from packet_utils import dump_json, ensure_packet_dir, parse_generation_prompts, read_brand_product, slug
from reference_selector import is_safe_reference_url, pick_auto_reference_url

try:  # pragma: no cover - optional dependency
    from PIL import Image
except Exception:  # pragma: no cover - optional dependency
    Image = None  # type: ignore

RATIO_SIZE_MAP: Dict[str, Dict[str, Tuple[int, int] | str]] = {
    "1:1": {"provider_size": "1024x1024", "final_dimensions": (1024, 1024)},
    "4:5": {"provider_size": "1024x1536", "final_dimensions": (1024, 1280)},
    "9:16": {"provider_size": "1024x1536", "final_dimensions": (1080, 1920)},
    "16:9": {"provider_size": "1536x1024", "final_dimensions": (1920, 1080)},
}


def normalize_ratio(value: str | None) -> str:
    raw = str(value or "1:1").strip().lower().replace("x", ":")
    return raw if raw in RATIO_SIZE_MAP else "1:1"


def parse_size(size: str) -> Tuple[int, int]:
    try:
        left, right = size.lower().split("x", 1)
        width, height = int(left), int(right)
        if width <= 0 or height <= 0:
            raise ValueError
        return width, height
    except Exception as exc:
        raise ValueError(f"invalid size: {size}") from exc


def resolve_render_spec(*, ratio: str, requested_size: str) -> Dict[str, Any]:
    normalized_ratio = normalize_ratio(ratio)
    mapped = RATIO_SIZE_MAP[normalized_ratio]
    provider_size = str(mapped["provider_size"]) if requested_size == "auto" else requested_size
    final_dimensions = tuple(mapped["final_dimensions"])  # type: ignore[arg-type]
    return {
        "requested_ratio": normalized_ratio,
        "provider_size": provider_size,
        "provider_dimensions": parse_size(provider_size),
        "final_dimensions": final_dimensions,
    }


def make_solid_png(width: int, height: int, rgb: Tuple[int, int, int] = (242, 242, 242)) -> bytes:
    row = bytes([0]) + bytes([rgb[0], rgb[1], rgb[2]]) * width
    raw = row * height
    compressed = zlib.compress(raw, level=9)

    def chunk(tag: bytes, payload: bytes) -> bytes:
        crc = zlib.crc32(tag + payload) & 0xFFFFFFFF
        return struct.pack(">I", len(payload)) + tag + payload + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", compressed)
        + chunk(b"IEND", b"")
    )


def parse_png_dimensions(data: bytes) -> Optional[Tuple[int, int]]:
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", data[16:24])


def image_dimensions_from_path(path: Path) -> Optional[Tuple[int, int]]:
    try:
        return parse_png_dimensions(path.read_bytes())
    except Exception:
        return None


def postprocess_to_ratio(image_bytes: bytes, target_dims: Tuple[int, int]) -> Tuple[bytes, Tuple[int, int], str]:
    if Image is None:  # pragma: no cover - optional dependency
        parsed = parse_png_dimensions(image_bytes)
        return image_bytes, parsed or target_dims, "none:pillow_unavailable"

    with Image.open(io.BytesIO(image_bytes)) as img:  # pragma: no cover - exercised only in live mode
        src_w, src_h = img.size
        target_w, target_h = target_dims
        src_ratio = src_w / src_h
        target_ratio = target_w / target_h
        if src_ratio > target_ratio:
            crop_w = int(src_h * target_ratio)
            left = max(0, (src_w - crop_w) // 2)
            box = (left, 0, left + crop_w, src_h)
        else:
            crop_h = int(src_w / target_ratio)
            top = max(0, (src_h - crop_h) // 2)
            box = (0, top, src_w, top + crop_h)
        cropped = img.convert("RGB").crop(box)
        final = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
        out = io.BytesIO()
        final.save(out, format="PNG")
        return out.getvalue(), (target_w, target_h), "center-crop+resize:pillow"


class OpenAIImageProvider:
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str, size: str, reference_image_path: Optional[Path] = None) -> Tuple[bytes, str]:
        if reference_image_path:
            return self._generate_with_reference(prompt, size, reference_image_path)
        return self._generate_text_only(prompt, size)

    def _generate_text_only(self, prompt: str, size: str) -> Tuple[bytes, str]:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "size": size,
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

        return extract_openai_image_bytes(body), "images/generations"

    def _generate_with_reference(self, prompt: str, size: str, reference_image_path: Path) -> Tuple[bytes, str]:
        image_bytes = reference_image_path.read_bytes()
        mime_type = mimetypes.guess_type(reference_image_path.name)[0] or "image/png"
        filename = reference_image_path.name

        # Some API variants accept `image[]`; others accept `image`. Try both.
        attempts = [("image[]",), ("image",)]
        last_error = ""
        for field_name_tuple in attempts:
            field_name = field_name_tuple[0]
            boundary = f"----brandshootkit-{uuid.uuid4().hex}"
            body = build_multipart_form_data(
                boundary=boundary,
                fields={
                    "model": self.model,
                    "prompt": prompt,
                    "size": size,
                },
                files=[(field_name, filename, mime_type, image_bytes)],
            )
            req = urllib.request.Request(
                "https://api.openai.com/v1/images/edits",
                data=body,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": f"multipart/form-data; boundary={boundary}",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=180) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                return extract_openai_image_bytes(payload), f"images/edits:{field_name}"
            except urllib.error.HTTPError as exc:
                details = exc.read().decode("utf-8", errors="replace")
                last_error = f"OpenAI image edit failed ({exc.code}) [{field_name}]: {details}"
                if exc.code not in {400, 404, 409, 415, 422}:
                    raise RuntimeError(last_error) from exc
            except urllib.error.URLError as exc:
                raise RuntimeError(f"OpenAI request failed: {exc}") from exc

        raise RuntimeError(last_error or "OpenAI image edit failed for unknown reason")


def build_multipart_form_data(
    *,
    boundary: str,
    fields: Dict[str, str],
    files: List[Tuple[str, str, str, bytes]],
) -> bytes:
    chunks: List[bytes] = []

    for name, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        chunks.append(str(value).encode("utf-8"))
        chunks.append(b"\r\n")

    for field_name, filename, mime_type, data in files:
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(
            (
                f'Content-Disposition: form-data; name="{field_name}"; '
                f'filename="{filename}"\r\n'
            ).encode("utf-8")
        )
        chunks.append(f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"))
        chunks.append(data)
        chunks.append(b"\r\n")

    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks)


def extract_openai_image_bytes(body: Dict[str, Any]) -> bytes:
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
    p.add_argument(
        "--size",
        default="auto",
        help="Provider size override in live mode (default: auto ratio-aware mapping)",
    )
    p.add_argument("--limit", type=int, default=0, help="Optional shot limit for quick runs")
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing image files")
    p.add_argument("--asset-ids", default="", help="Comma-separated asset IDs to generate (default: all)")
    p.add_argument("--prompt-overrides", help="JSON map of asset_id -> prompt override")
    p.add_argument(
        "--reference-image",
        help="Reference image file path or URL; used in live mode and cached inside the packet",
    )
    p.add_argument(
        "--auto-reference-image",
        dest="auto_reference_image",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Auto-select reference from scout.json image_evidence/image_urls for live packet runs",
    )
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


def write_placeholder(path: Path, shot: Dict[str, Any], final_dimensions: Tuple[int, int]) -> None:
    width, height = final_dimensions
    path.write_bytes(make_solid_png(width, height))
    sidecar = path.with_suffix(".placeholder.txt")
    sidecar.write_text(
        "\n".join(
            [
                "dry_run_placeholder=true",
                f"asset_id={shot['asset_id']}",
                f"shot_name={shot['shot_name']}",
                f"ratio={shot['ratio']}",
                f"dimensions={width}x{height}",
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


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def image_extension_for(url_or_path: str, content_type: str = "") -> str:
    parsed = urlparse(url_or_path)
    ext = Path(parsed.path if parsed.scheme else url_or_path).suffix.lower()
    if ext in {".png", ".jpg", ".jpeg", ".webp"}:
        return ".jpg" if ext == ".jpeg" else ext
    if "image/png" in content_type:
        return ".png"
    if "image/jpeg" in content_type:
        return ".jpg"
    if "image/webp" in content_type:
        return ".webp"
    return ".png"


def cache_reference_image(
    source: str,
    *,
    packet_dir: Path,
    allow_network: bool,
) -> Dict[str, Optional[str]]:
    cache_dir = packet_dir / "assets" / "reference-images"
    cache_dir.mkdir(parents=True, exist_ok=True)
    if is_url(source):
        if not allow_network:
            raise RuntimeError("reference image URL caching is disabled outside live mode")
        if not is_safe_reference_url(source):
            raise RuntimeError(f"reference URL blocked as unsafe: {source}")
        req = urllib.request.Request(
            source,
            headers={"User-Agent": "brand-shoot-kit/0.2"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read()
                content_type = str(resp.headers.get("Content-Type", "")).lower()
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"reference image download failed ({exc.code}): {details}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"reference image download failed: {exc}") from exc

        if not body:
            raise RuntimeError("reference image download returned empty body")
        ext = image_extension_for(source, content_type)
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
        out_path = cache_dir / f"reference-url-{digest}{ext}"
        out_path.write_bytes(body)
        return {"reference_image_path": str(out_path), "reference_image_url": source}

    local = Path(source).expanduser().resolve()
    if not local.exists():
        raise RuntimeError(f"reference image file not found: {local}")
    if not local.is_file():
        raise RuntimeError(f"reference image path is not a file: {local}")
    ext = image_extension_for(str(local))
    digest = hashlib.sha256(str(local).encode("utf-8")).hexdigest()[:16]
    out_path = cache_dir / f"reference-local-{digest}{ext}"
    if local != out_path:
        shutil.copy2(local, out_path)
    return {"reference_image_path": str(out_path), "reference_image_url": None}


def resolve_reference_image(
    *,
    args: argparse.Namespace,
    packet_dir: Path,
    mode: str,
) -> Tuple[Optional[Path], Optional[str], List[str], str]:
    notes: List[str] = []
    source: Optional[str] = args.reference_image
    auto_selected = False

    auto_default = bool(args.live and args.packet)
    auto_enabled = args.auto_reference_image if args.auto_reference_image is not None else auto_default

    if not source and auto_enabled and mode == "live":
        source = pick_auto_reference_url(packet_dir)
        if source:
            auto_selected = True
            notes.append("auto_reference_image:selected_from_scout")
        else:
            notes.append("auto_reference_image:no_safe_candidate_found")
    elif not source and auto_enabled and mode != "live":
        notes.append("auto_reference_image:skipped_non_live_mode")

    if not source:
        return None, None, notes, "none"

    try:
        cached = cache_reference_image(source, packet_dir=packet_dir, allow_network=(mode == "live"))
    except Exception as exc:
        notes.append(f"reference_image_error:{exc}")
        return None, source if is_url(source) else None, notes, "none"

    ref_path = Path(cached["reference_image_path"]) if cached["reference_image_path"] else None
    ref_url = cached["reference_image_url"]
    source_mode = "auto" if auto_selected else "explicit"
    return ref_path, ref_url, notes, source_mode


def main() -> int:
    args = parse_args()
    if args.size != "auto":
        try:
            parse_size(args.size)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
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
        provider = OpenAIImageProvider(os.environ["OPENAI_API_KEY"], args.model)
        mode = "live"

    reference_image_path, reference_image_url, reference_notes, reference_mode = resolve_reference_image(
        args=args,
        packet_dir=packet_dir,
        mode=mode,
    )

    run_stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    entries: List[Dict[str, Any]] = []

    for shot in shots:
        render_spec = resolve_render_spec(ratio=str(shot.get("ratio", "1:1")), requested_size=args.size)
        requested_ratio = render_spec["requested_ratio"]
        provider_size = render_spec["provider_size"]
        final_dimensions = tuple(render_spec["final_dimensions"])
        filename = deterministic_file_name(shot)
        image_path = out_dir / filename

        if image_path.exists() and not args.overwrite:
            existing_dimensions = image_dimensions_from_path(image_path)
            entries.append(
                {
                    **shot,
                    "status": "skipped-existing",
                    "provider": mode,
                    "dry_run": mode != "live",
                    "image_path": str(image_path),
                    "requested_ratio": requested_ratio,
                    "provider_size": provider_size,
                    "final_dimensions": list(existing_dimensions or final_dimensions),
                    "reference_image_path": str(reference_image_path) if reference_image_path else None,
                    "reference_image_url": reference_image_url,
                }
            )
            continue

        entry = {
            **shot,
            "status": "generated",
            "provider": mode,
            "dry_run": mode != "live",
            "image_path": str(image_path),
            "requested_ratio": requested_ratio,
            "provider_size": provider_size,
            "final_dimensions": list(final_dimensions),
            "reference_image_path": str(reference_image_path) if reference_image_path else None,
            "reference_image_url": reference_image_url,
        }

        if mode == "live" and provider is not None:
            try:
                provider_bytes, endpoint_used = provider.generate(
                    shot["prompt"],
                    provider_size,
                    reference_image_path=reference_image_path,
                )
                output_bytes, actual_dims, postprocess_mode = postprocess_to_ratio(provider_bytes, final_dimensions)
                image_path.write_bytes(output_bytes)
                entry["image_sha256"] = hashlib.sha256(output_bytes).hexdigest()
                entry["openai_image_endpoint"] = endpoint_used
                entry["postprocess_mode"] = postprocess_mode
                entry["final_dimensions"] = list(actual_dims)
            except Exception as exc:  # pragma: no cover
                entry["status"] = "error"
                entry["error"] = str(exc)
        else:
            write_placeholder(image_path, shot, final_dimensions)
            placeholder_bytes = image_path.read_bytes()
            entry["image_sha256"] = hashlib.sha256(placeholder_bytes).hexdigest()
            entry["postprocess_mode"] = "dry-run:rendered-at-target-size"

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
        "reference_image_mode": reference_mode,
        "reference_image_path": str(reference_image_path) if reference_image_path else None,
        "reference_image_url": reference_image_url,
        "reference_image_notes": reference_notes,
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
