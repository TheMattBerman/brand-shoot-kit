# Codex Review Recommendations: Brand Shoot Kit

Date: April 27, 2026
Reviewer mode: product/agent-system audit (not code-style review)

## 1. Executive verdict

### Maturity score today
- Overall maturity: **5.4 / 10**

### What this currently is
- Brand Shoot Kit is currently a **deterministic dry-run production scaffold with optional live hooks**, not yet a production-grade visual generation system.
- It is stronger than a pure planning/spec kit because it has runnable orchestration, generation, QA, and export scripts (`scripts/run-brand-shoot.py`, `scripts/generate-images.py`, `scripts/qa-images.py`, `scripts/export-packager.py`) and a passing local smoke path (`scripts/run-smoke.sh`).
- It is not yet an “actual product” in the sense of proven live output quality, closed-loop rerolls, or evidence-backed module intelligence.

### Are the 8 subskills truly useful or thin wrappers?
- Current answer: **mostly thin wrappers around the root workflow + scripts**.
- The 8 subskills are directionally correct in decomposition, but each `skills/*/SKILL.md` is mostly behavioral guidance with little module-owned executable depth.
- There are no module-specific executables/artifacts per subskill (for example, no dedicated `visual-gap-audit` engine, no real `memory-writer` updater, no autonomous `qa-reroll` runner).

## 2. What's missing

### Missing product capabilities
- Real, validated live generation quality loop across categories (today’s reliable path is dry-run placeholders).
- Closed-loop reroll execution (fail -> rewrite -> regenerate -> re-score) rather than “reroll instruction only”.
- Real channel variant production (crop/resize/compression) versus copy-only export packaging.
- Strong extraction for product truth (variants, claims, ingredients/specs, structured label details).

### Missing skill depth
- Subskills do not currently own concrete I/O transforms beyond text contracts:
  - `brand-scout` delegates to a basic HTML scout script.
  - `product-preservation`, `visual-gap-audit`, `shoot-director`, `prompt-factory` are mostly implicit inside `create-shoot-packet.py` templates.
  - `qa-reroll` does not execute rerolls.
  - `memory-writer` does not persist learned deltas from QA history.
- Module contracts in `references/module-contracts/*.md` describe JSON artifacts (`preservation.json`, `visual-gaps.json`, `shoot-plan.json`, `prompts.json`) that are not actually first-class outputs today.

### Missing scripts/automation
- No script that applies QA reject queue into regenerated shots automatically.
- No script that converts module contracts into independently rerunnable pipeline steps.
- No regression harness that asserts category-differentiated strategy/prompt behavior from scout input.

### Missing evals/tests
- Evals are mostly prose checklists (`evals/trigger-evals.md`, `evals/execution-evals.md`, `evals/output-quality-rubric.md`) not executable gates.
- No CI-style fail thresholds for output quality, fidelity errors, reroll convergence, or prompt drift.
- No fixture-based truth tests for label preservation and distortion risks.

### Missing examples/assets
- Example packets exist but are mostly document outputs, not golden “input -> generated assets -> QA logs -> accepted exports” runs.
- No canonical side-by-side of pass/fail live outputs for different product classes.

### Missing installation/distribution polish
- Install lifecycle is good (`install.sh`, `doctor.sh`, `uninstall.sh`), but no release/dist packaging workflow comparable to stronger kits.
- No versioned release artifact process or changelog discipline tied to behavioral guarantees.

### Missing UX/onboarding
- Good README quickstart, but limited operator playbook for real production use: confidence gating, decision boundaries, recovery flows, and live-cost controls are under-specified.
- No “first successful real run” guided demo with expected outputs and quality bars.

## 3. Layers of quality (L0-L5)

- **L0: Spec only**
  - Docs and positioning, no runnable path.
- **L1: Skill scaffold**
  - SKILL files and references; mostly advisory.
- **L2: Deterministic dry-run pipeline**
  - Runnable end-to-end with placeholders/manifests; deterministic QA/export scaffolding.
- **L3: Live generation + manual QA**
  - Real provider outputs and reviewer workflow with usable acceptance controls.
- **L4: Automated QA/reroll/export**
  - Failures rerolled automatically, convergence tracked, exports variant-ready by channel.
- **L5: Production-grade agent kit**
  - Golden datasets, executable eval gates, stable module contracts, memory compounding, release/CI rigor, proven outcomes across categories.

### Honest placement
- **Brand Shoot Kit is at L2 today, with partial L3 hooks.**
- Evidence:
  - `scripts/run-smoke.sh` passes deterministically.
  - `scripts/generate-images.py` defaults to dry-run placeholders.
  - `scripts/qa-images.py` defaults to deterministic-manual scoring.
  - Live modes exist behind `--live`, but are not yet proven by robust evals.

## 4. Comparison to previous/stronger agent kits

## Meta Ads Kit (`/home/matt/clawd/projects/meta-ads-kit`)

### Stronger than Brand Shoot Kit in
- Operational agent loop integration for reporting and actions (`run.sh`, `skills/meta-ads/scripts/meta-ads.sh`).
- Real external-system action scripts in at least part of the stack (notably `skills/pixel-capi/scripts/*.sh`, including real send/audit/test utilities).
- Deeper operator framing and workflow memory/approval patterns in docs.

### Weaker or similar
- Some capabilities (notably `ad-upload`) are still heavily instruction-driven in SKILL docs rather than packaged executable scripts.
- So Meta Ads Kit also has “doc-heavy capability claims” in places.

### Net comparison
- Brand Shoot Kit has cleaner deterministic offline flow than many skill-only kits.
- Meta Ads Kit demonstrates stronger real-world integration depth in core reporting and pixel/CAPI tooling.

## Google Ads Copilot (`/home/matt/clawd/workspace/google-ads-copilot`)

### Stronger than Brand Shoot Kit in
- Mature multi-layer architecture with clear Read -> Draft -> Apply separation.
- Real apply/undo/audit tooling (`scripts/apply-layer/gads-apply.sh`, `gads-undo.sh`, supporting libs).
- Executable eval harness (`evals/run.py`, JSON cases/fixtures), not only prose eval docs.
- Packaging/distribution maturity (`scripts/package/build-release.sh`, `build-dist.sh`, release docs).
- Workspace memory + operator workflow rigor is significantly more developed.

### Net comparison
- Google Ads Copilot is a clear **L4-ish system in discipline**, while Brand Shoot Kit is **L2 with L3 hooks**.

## Content Radar / Content DNA / Content DNA Batch

### Stronger than Brand Shoot Kit in
- True script-backed skill execution in individual skills (`content-radar.sh`, `content-dna.sh` + `analyze.py`, `content-dna-batch.sh`).
- Real batch/parallel pipelines and aggregation behavior.
- Better signal-processing identity (inputs -> transforms -> outputs) per skill.

### Caveat
- These skills include API dependencies and some key handling quality issues, but they still show deeper module ownership than Brand Shoot’s subskills.

## Image Prompt Builder / BigSkills

- `image-prompt-builder` is mostly guidance/reference heavy.
- `bigskills` provides strong quality rubric and operational expectations; against that standard, Brand Shoot Kit is correctly challenged as underbuilt in module depth/eval automation.

## 5. Recommendations for improvement

## P0: Must do next

### P0.1 Implement real module artifact pipeline (not just monolithic packet writer)
- Why it matters:
  - Without module-owned artifacts, subskills remain wrappers and drift is hard to debug.
- Change:
  - Split `scripts/create-shoot-packet.py` logic into module outputs:
    - `scout.json` (already basic)
    - `preservation.json`
    - `visual-gaps.json`
    - `shoot-plan.json`
    - `prompts.json`
  - Wire `scripts/run-brand-shoot.py` to execute each stage and persist each artifact.
  - Align outputs with `references/module-contracts/*.md`.
- Acceptance criteria:
  - Running URL/scout flow produces all contract artifacts in packet directory.
  - Each artifact can be regenerated independently from prior artifact(s).
  - Packet docs render from artifacts, not from hidden template logic.
- Rough difficulty: **M**

### P0.2 Build automatic reroll executor
- Why it matters:
  - QA without automated correction loop is operationally incomplete.
- Change:
  - Add `scripts/reroll-failed.py` (or extend `qa-images.py`) to read `qa-results.json`, rewrite failed prompts, regenerate failed shots, and append reroll history.
- Acceptance criteria:
  - For failed live shots, system executes up to N rerolls automatically.
  - New manifest version tracks original + reroll attempts + final status.
  - Convergence stats emitted (`pass_after_reroll`, `reroll_exhausted`).
- Rough difficulty: **M/L**

### P0.3 Create executable eval harness
- Why it matters:
  - Prose evals cannot prevent regressions.
- Change:
  - Add `evals/run.py` (fixture-driven) similar in spirit to Google Ads Copilot.
  - Add fixture packets + expected thresholds (structure, fidelity flags, prompt quality indicators, reroll convergence).
- Acceptance criteria:
  - One command returns pass/fail and non-zero exit on regression.
  - Thresholds are explicit and versioned.
- Rough difficulty: **M**

## P1: High leverage

### P1.1 Deepen `brand-scout` extraction quality
- Why it matters:
  - Preservation and prompts are only as good as source evidence quality.
- Change:
  - Upgrade `scripts/scout-url.sh` and/or add `scripts/scout-structured.py` for product schema extraction, variants, claims, ingredients/specs, and confidence scoring.
- Acceptance criteria:
  - At least 4 category fixtures extract structured truth fields with confidence.
  - Low-confidence fields are explicitly marked and influence downstream conservatism.
- Rough difficulty: **M**

### P1.2 Turn subskills into module owners
- Why it matters:
  - Current subskills are mostly guidance docs; they need executable ownership.
- Change:
  - Add module scripts under each skill or a mapped module folder (e.g., `skills/visual-gap-audit/scripts/...`).
  - Ensure each subskill has a direct invocation path and clear input/output artifact contract.
- Acceptance criteria:
  - Each of the 8 subskills can run independently on artifacts and update outputs deterministically.
  - `doctor.sh` validates per-module executable checks.
- Rough difficulty: **L**

### P1.3 Add golden run bundles
- Why it matters:
  - Real trust needs proven outputs, not only generated docs.
- Change:
  - Add 2-3 golden product-category runs containing source input, generated assets, QA results, reroll logs, final exports.
- Acceptance criteria:
  - Golden runs are reproducible and referenced in README.
  - Differences from expected outputs are tracked.
- Rough difficulty: **M**

## P2: Polish/scale

### P2.1 Release packaging and versioned changelog discipline
- Why it matters:
  - Easier adoption and safer upgrades.
- Change:
  - Add `scripts/package/build-dist.sh` + release notes process.
- Acceptance criteria:
  - Versioned installable bundle generated from CI/local script.
- Rough difficulty: **S/M**

### P2.2 Operator playbook + live-cost control UX
- Why it matters:
  - Helps users run live mode safely and consistently.
- Change:
  - Add `OPERATOR-PLAYBOOK.md` with explicit live gating, budget caps, reroll limits, stop conditions.
- Acceptance criteria:
  - New user can execute one real run with clear go/no-go decisions at each stage.
- Rough difficulty: **S**

### P2.3 Better onboarding demos
- Why it matters:
  - Adoption friction drops when users see one full successful example quickly.
- Change:
  - Add a guided demo workflow doc and expected outputs tree.
- Acceptance criteria:
  - First-run completion time and confusion drop materially (qualitative but observable).
- Rough difficulty: **S**

## 6. Suggested build sequence (3 passes)

## Pass 1: Make it actually generate + QA one real product
- Goal:
  - Prove one live category run with real outputs and QA decisions.
- Work:
  - Stabilize live path in `generate-images.py` + `qa-images.py`.
  - Add reroll executor for failed shots.
  - Record one golden run bundle (input, outputs, QA, exports).
- Exit criteria:
  - 12-shot live run completes with explicit pass/fail statuses and reroll attempts logged.

## Pass 2: Make the suite skills genuinely deep
- Goal:
  - Convert subskills from wrappers to module owners.
- Work:
  - Implement contract artifacts and per-module scripts.
  - Ensure `run-brand-shoot.py` orchestrates explicit stage artifacts.
  - Add per-module tests/fixtures.
- Exit criteria:
  - Each module runnable independently; artifacts are stable and traceable.

## Pass 3: Package/demo/eval quality
- Goal:
  - Move from strong prototype to deployable agent kit.
- Work:
  - Add executable eval harness + thresholds.
  - Add release packaging scripts and changelog discipline.
  - Add operator playbook and guided demos.
- Exit criteria:
  - One command validates quality gates; install/release path is reproducible; demo flow is deterministic.

## 7. Brutal final note

Brand Shoot Kit is promising because it already has an executable spine, not just strategy prose. But Matt’s skepticism is correct: today it is still an early system with strong framing and medium implementation depth, not a hardened product kit. The 8-subskill architecture is conceptually right but functionally shallow until each module owns real artifact transforms, automated reroll behavior, and executable quality gates. Right now the repo proves “we can run a clean dry-run pipeline”; it does not yet prove “we can repeatedly produce high-fidelity ecommerce assets with production reliability.”

## Evidence highlights used for this review

- Brand Shoot Kit:
  - `/home/matt/clawd/projects/brand-shoot-kit/scripts/run-smoke.sh`
  - `/home/matt/clawd/projects/brand-shoot-kit/scripts/run-brand-shoot.py`
  - `/home/matt/clawd/projects/brand-shoot-kit/scripts/create-shoot-packet.py`
  - `/home/matt/clawd/projects/brand-shoot-kit/scripts/generate-images.py`
  - `/home/matt/clawd/projects/brand-shoot-kit/scripts/qa-images.py`
  - `/home/matt/clawd/projects/brand-shoot-kit/scripts/export-packager.py`
  - `/home/matt/clawd/projects/brand-shoot-kit/skills/*/SKILL.md`
  - `/home/matt/clawd/projects/brand-shoot-kit/references/module-contracts/*.md`
  - Smoke run verified on April 27, 2026; output showed dry-run generation, deterministic-manual QA, deterministic copy packaging.
- Comparison repos:
  - `/home/matt/clawd/projects/meta-ads-kit/README.md`
  - `/home/matt/clawd/projects/meta-ads-kit/skills/meta-ads/scripts/meta-ads.sh`
  - `/home/matt/clawd/projects/meta-ads-kit/skills/pixel-capi/scripts/*.sh`
  - `/home/matt/clawd/workspace/google-ads-copilot/ARCHITECTURE.md`
  - `/home/matt/clawd/workspace/google-ads-copilot/scripts/apply-layer/*.sh`
  - `/home/matt/clawd/workspace/google-ads-copilot/evals/run.py`
  - `/home/matt/clawd/skills/content-radar/scripts/content-radar.sh`
  - `/home/matt/clawd/skills/content-dna/scripts/content-dna.sh`
  - `/home/matt/clawd/skills/content-dna-batch/scripts/content-dna-batch.sh`
