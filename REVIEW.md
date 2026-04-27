# Brand Shoot Kit Critical Review (April 27, 2026)

## Current Maturity Score

- **Overall maturity: 4.2 / 10 (early alpha)**
- **BigSkills score: 29 / 45 (major revision needed, not ship-level yet)**

BigSkills rubric breakdown:
- Trigger Quality: 4/5
- Behavior Shift: 3/5
- Taste Transfer: 3/5
- Anti-Slop Defense: 4/5
- Deliverable Power: 2/5
- Token Discipline: 4/5
- Architecture Quality: 3/5
- Operational Completeness: 4/5
- Reusability: 2/5

## What Is Genuinely Good

- Core positioning is clear: ecommerce visual production, not ad-spy.
- SKILL voice and non-negotiables are strong and mostly behavior-shifting.
- References are useful and mostly practical, not fluffy.
- Operational scaffolding exists (`install`, `doctor`, `uninstall`, eval docs, examples).
- Graceful degradation is intentional and mostly honest.

## What Is Shallow / Scaffold-Only

- The main system behavior is still template expansion, not evidence-driven direction.
- `create-shoot-packet.py` outputs mostly generic defaults regardless of product nuances.
- Example packets are visibly synthetic and repetitive; they do not prove strong output quality.
- Evals are currently statement-based docs, not executable quality gates.
- No real module handoffs with explicit artifacts between stages.

## Where One Skill Is Insufficient

A single `SKILL.md` can enforce process order, but this product needs independent modules with testable contracts:
- scouting/extraction quality is a separate engineering problem
- preservation and compliance gating must run independently
- prompt generation must consume real evidence and risk profile
- QA/reroll needs executable loop logic, not checklist text
- export packaging/cropping/versioning should be deterministic

Without modularization, quality cannot be debugged stage-by-stage and drift is inevitable.

## Recommended Skill/Module Architecture

Recommended suite:
- `brand-scout`: URL + image evidence extraction, confidence scoring
- `product-preservation`: immutable product truth contract
- `visual-gap-audit`: conversion-priority gap matrix
- `shoot-director`: direction choice + 12-shot production plan
- `prompt-factory`: operational prompts with reroll playbooks
- `qa-reroll`: criterion scoring + reject queue + correction prompts
- `export-packager`: asset mapping, naming, channel variants
- `memory-writer`: preserve wins/fails for next run

The repo now includes a first-pass suite architecture doc and module contracts, but only part of this is executable.

## Key Gaps (By Capability)

- Scripts:
  - Provider-backed generation/QA/export scripts now exist, but live mode quality is uncalibrated and dry-run is still the default path.
  - No automated reroll executor yet (reject reasons are produced, but failed shots are not regenerated automatically).
  - Export is deterministic copy packaging; crop/resize variants per channel are not implemented yet.
- Browser/data extraction:
  - `scout-url.sh` is useful but basic HTML parsing only.
  - No robust structured product extraction (variants, claims, ingredients, specs).
- Real image generation:
  - Integrated behind explicit `--live` flags (`generate-images.py`, `qa-images.py`) and env checks.
  - Doctor/smoke remain no-spend dry-run by design.
- QA:
  - Deterministic/manual QA and optional vision-based scoring now exist.
  - No closed-loop reroll execution yet.
- Examples:
  - Current example packets are formulaic and not “golden quality” artifacts.
- Evals:
  - Not executable enough to block regressions.
- Memory:
  - Placeholder files only; no update logic.
- Installability/productization:
  - Install story is decent, but no release packaging (`dist/`) and no multi-skill installation mode.

## Priority Roadmap

## Immediate Next Build (this week)

- URL/scout JSON -> packet deterministic orchestrator (now added).
- Module architecture + explicit contracts (now added).
- Offline smoke test wired into doctor (now added).

## v0.2

- Add real generation script (`generate-images.py`) with OpenAI provider support. (Implemented: dry-run + optional live)
- Add `qa-images.py` vision scoring script producing machine-readable pass/fail output. (Implemented: deterministic/manual + optional live vision)
- Upgrade prompt output from generic templates to category-aware shot directives using scout evidence. (Implemented)
- Add deterministic packaging pipeline (`export-packager.py`) and end-to-end smoke coverage. (Implemented)

## v0.3

- Add structured extraction pipeline (variants, claims, pack text, key ingredients/specs).
- Add reroll automation that consumes QA reject reasons and rewrites prompts per shot.
- Replace placeholder memory with persistent per-product shot memory updates.

## v1.0

- End-to-end pipeline: URL -> evidence -> generation -> QA reroll -> export pack.
- Executable eval suite with threshold gates and baseline comparison.
- Golden examples with real generated assets and QA traces.
- Multi-skill suite install mode with modular invocation paths.

## Acceptance Criteria For “Actually Good Now”

A release is truly good only when all are true:
- Given a real product URL, system generates a full packet plus at least 12 images and channel exports.
- At least 90% of images pass product preservation checks without manual intervention.
- QA loop auto-rerolls failed shots and converges within 2 rerolls for >=80% of failures.
- Visual gap audit and shot plan differ materially across product categories (not template clones).
- Eval suite is executable and enforced in CI/doctor with clear pass/fail thresholds.
- Two real-world golden runs (different categories) are included with assets and QA logs.
- Module contracts are stable and each module has deterministic I/O artifacts.

## Bottom Line

Matt’s “this still feels early” diagnosis is correct.

This repo has a strong strategic frame and decent scaffolding, but it is still a planning kit, not yet a production-grade visual system. The path to real value is not more prose; it is executable modular pipeline depth.
