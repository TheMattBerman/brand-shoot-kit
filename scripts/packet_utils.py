#!/usr/bin/env python3
"""Shared packet parsing helpers for Brand Shoot Kit scripts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

SHOT_HEADER_RE = re.compile(r"^##\s+Shot\s+(\d+)\s+-\s+(.+?)\s*$", re.MULTILINE)


def slug(value: str) -> str:
    out = "".join(c.lower() if c.isalnum() else "-" for c in value)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-") or "item"


def ensure_packet_dir(packet_dir: Path) -> None:
    required = [
        packet_dir / "00-brand-analysis.md",
        packet_dir / "04-generation-prompts.md",
        packet_dir / "05-qa-report.md",
        packet_dir / "06-export-map.md",
        packet_dir / "assets",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Packet missing required paths: {missing}")


def parse_generation_prompts(prompts_path: Path) -> List[Dict[str, Any]]:
    text = prompts_path.read_text(encoding="utf-8")
    matches = list(SHOT_HEADER_RE.finditer(text))
    shots: List[Dict[str, Any]] = []

    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end].strip()

        idx = int(m.group(1))
        name = m.group(2).strip()

        use_case = _extract_single(block, r"\*\*Use case:\*\*\s*(.+)")
        ratio = _extract_single(block, r"\*\*Aspect ratio:\*\*\s*(.+)")
        prompt = _extract_block(block, "**Prompt:**", ["**Negative constraints:**", "**Reroll if failed:**"])
        negatives = _extract_bullets(block, "**Negative constraints:**")
        reroll = _extract_block(block, "**Reroll if failed:**", [])

        shots.append(
            {
                "shot_index": idx,
                "asset_id": f"shot-{idx:02d}",
                "shot_name": name,
                "use_case": use_case,
                "ratio": ratio,
                "prompt": prompt,
                "negative_constraints": negatives,
                "reroll_if_failed": reroll,
            }
        )

    return shots


def _extract_single(text: str, pattern: str) -> str:
    m = re.search(pattern, text)
    if not m:
        return "unknown"
    return " ".join(m.group(1).split()).strip()


def _extract_block(text: str, marker: str, stop_markers: List[str]) -> str:
    if marker not in text:
        return ""
    start = text.index(marker) + len(marker)
    tail = text[start:].lstrip("\n")
    end = len(tail)
    for stop in stop_markers:
        pos = tail.find(stop)
        if pos != -1:
            end = min(end, pos)
    chunk = tail[:end].strip()
    return " ".join(chunk.split())


def _extract_bullets(text: str, marker: str) -> List[str]:
    if marker not in text:
        return []
    start = text.index(marker) + len(marker)
    tail = text[start:].lstrip("\n")
    stop = tail.find("**Reroll if failed:**")
    if stop != -1:
        tail = tail[:stop]
    out = []
    for line in tail.splitlines():
        line = line.strip()
        if line.startswith("- "):
            out.append(line[2:].strip())
    return out


def parse_export_map(export_map_path: Path) -> Dict[str, str]:
    text = export_map_path.read_text(encoding="utf-8")
    lines = [ln.strip() for ln in text.splitlines()]
    channel_by_shot: Dict[str, str] = {}

    for line in lines:
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 3:
            continue
        shot, best_use = parts[0], parts[1]
        if shot.lower() in {"shot", "---"}:
            continue
        channel_by_shot[shot] = best_use

    return channel_by_shot


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def read_brand_product(brand_analysis_path: Path) -> Dict[str, str]:
    text = brand_analysis_path.read_text(encoding="utf-8")
    return {
        "brand": _extract_from_bullet(text, "Brand"),
        "product": _extract_from_bullet(text, "Product"),
    }


def _extract_from_bullet(text: str, key: str) -> str:
    pat = rf"-\s*{re.escape(key)}:\s*(.+)"
    m = re.search(pat, text)
    return m.group(1).strip() if m else "unknown"


def latest_run_dir(parent: Path, prefix: str) -> Optional[Path]:
    if not parent.exists():
        return None
    runs = sorted([p for p in parent.iterdir() if p.is_dir() and p.name.startswith(prefix)])
    return runs[-1] if runs else None
