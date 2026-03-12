# Python SDK Examples

These examples are portable and do not use hardcoded local paths.
DocQuery CLI parity in SDK: 10 operations (`client.projects.list` + 9 `project.docquery.*` methods, including `crop`).

Page-12 full command cookbook:
- `PAGE12_COOKBOOK.md`
- `page13cookbook.md`
- `REVIEWS_QUICKSTART.md`

## Prerequisites

```bash
pip install struai
export STRUAI_API_KEY=your_api_key
export STRUAI_BASE_URL=https://api.stru.ai  # optional
export STRUAI_PDF=/absolute/path/to/structural.pdf
```

## Scripts

```bash
# Runnable Page-12 cookbook (DocQuery traversal + crop)
python3 page12_cookbook.py

# Tier 1 drawings flow
python3 test_prod_page12.py --page 12

# Full Tier 1 + Tier 2 projects/docquery workflow
python3 test_prod_page12_full.py --page 12

# Full workflow with crop demo (server-side graph uuid crop)
python3 test_prod_page12_full.py --page 12 \
  --crop-output /absolute/path/to/crop.png

# Full workflow + cleanup
python3 test_prod_page12_full.py --page 12 --cleanup

# Async full workflow
python3 async_projects_workflow.py --page 12

# Review workflow (start + refresh)
python3 review_workflow.py --file-hash your_file_hash --pages 13

# Review workflow (wait for terminal status)
python3 review_workflow.py --file-hash your_file_hash --pages 13 --wait

# Page-13 review cookbook (create/status/questions/issues/stats/historical fetch)
python3 page13_review_cookbook.py
```
