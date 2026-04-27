# prompt-factory contract

Input:
- `shoot-plan.json`
- `preservation.json`

Output artifact:
- `prompts.json`

Required fields per shot:
- `use_case`, `ratio`, `prompt`, `negative_constraints[]`, `reroll_if_failed`

Quality gate:
- each prompt must mention preservation rules and a concrete reroll instruction.
