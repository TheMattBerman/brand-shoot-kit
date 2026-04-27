---
name: qa-reroll
description: "Score generated Brand Shoot Kit images for product accuracy, realism, brand fit, commerce usefulness, and artifact risk. Use for QA reports, reject queues, reroll decisions, and correction prompts."
metadata:
  openclaw:
    emoji: "✅"
    user-invocable: true
    primaryEnv: OPENAI_API_KEY
    requires:
      bins: ["python3"]
      env: []
---

# QA Reroll

Do not pass pretty failures.

## Score Gates

- product accuracy
- label/logo/text preservation
- realism/artifact risk
- brand fit
- channel usefulness
- composition clarity

## Reject Immediately

- changed packaging shape, count, or label text
- malformed hands or body interaction
- fake badges/certifications/claims
- product obscured or too small
- wrong variant/flavor/material

Use `scripts/qa-images.py --packet <packet>` to write structured QA results. Failed shots should produce concrete reroll instructions, not vague criticism.

Executable module owner path:
- `scripts/modules/qa_reroll.py --packet <packet-dir> --run-qa` -> updates `qa-results.json` and writes `reroll-manifest.json`
