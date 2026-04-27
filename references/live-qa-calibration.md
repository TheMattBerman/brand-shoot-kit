# Live QA Calibration (First Real Proof)

Use this immediately after the first real 3-shot proof run.

## Scope

This calibration is for human review of whether the kit is safe to scale from 3 shots to 12 shots.

## Human Review Checklist

1. Product accuracy
- Is the product shape/form factor correct?
- Is cap/dropper/pump/closure style correct?
- Are proportions believable and consistent?

2. Label fidelity
- Is visible label text faithful to the real product?
- Are brand/product names not mutated?
- Are legal/ingredient claims not hallucinated?

3. Realism and quality
- Is lighting physically plausible?
- Do reflections/shadows match scene context?
- Are textures/materials believable at commerce zoom levels?

4. Commerce usefulness
- Is framing usable for PDP/marketplace/social placements?
- Is the product sufficiently prominent?
- Are key details legible where needed?

5. Reroll quality
- Are reject reasons specific and actionable?
- Did reroll instructions address the true failure mode?
- Should reroll rubric or instructions be tightened?

## Threshold Tuning Guidance

- Raise QA threshold when images pass numeric score but fail label/product truth checks.
- Lower QA threshold only if false failures are blocking valid images and reviewer confidence remains high.
- Keep threshold changes small (+/- 2 to 5 points) and record why.

## Gate To Expand Beyond 3 Shots

Approve 12-shot expansion only if all are true:
- Product accuracy passes human review on all proof shots.
- No critical label fidelity issues.
- At least one shot is directly usable without reroll.
- Reroll reasons are coherent and improve outcomes.
- Reviewer signs off in `examples/live-proof-review-template.json` (copied into run folder).
