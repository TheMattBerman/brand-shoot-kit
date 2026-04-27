# product-preservation contract

Input:
- `scout.json`
- optional uploaded product images

Output artifact:
- `preservation.json`

Required fields:
- `product_type`
- `must_preserve[]`
- `can_vary[]`
- `never_change[]`
- `distortion_risks[]`
- `accuracy_confidence`

Failure mode:
- if confidence low, force conservative commerce-first shots.

Executable owner:
- `scripts/modules/product_preservation.py`
