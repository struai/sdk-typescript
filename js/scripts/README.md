# JavaScript SDK Example Scripts

Run from the repository `js/` directory.
DocQuery CLI parity in SDK: 10 operations (`client.projects.list` + 9 `project.docquery.*` methods, including `crop`).

## Prerequisites

```bash
npm install
npm run build
export STRUAI_API_KEY=your_api_key
export STRUAI_BASE_URL=https://api.stru.ai  # optional
export STRUAI_PDF=/absolute/path/to/structural.pdf
```

## Scripts

```bash
# Tier 1 drawings flow
STRUAI_PAGE=12 node scripts/drawings_quickstart.mjs

# Full Tier 1 + Tier 2 projects/docquery workflow
STRUAI_PAGE=12 node scripts/projects_workflow.mjs

# Full workflow + crop demo
STRUAI_PAGE=12 \
STRUAI_CROP_OUTPUT=/absolute/path/to/crop.png \
node scripts/projects_workflow.mjs

# Full workflow + cleanup
STRUAI_PAGE=12 STRUAI_CLEANUP=1 node scripts/projects_workflow.mjs

# Fast local surface smoke
node scripts/smoke_local.mjs

# Review workflow (start + refresh)
STRUAI_REVIEW_FILE_HASH=your_file_hash STRUAI_REVIEW_PAGES=13 \
node scripts/reviews_workflow.mjs

# Review workflow (wait for terminal status)
STRUAI_REVIEW_FILE_HASH=your_file_hash STRUAI_REVIEW_PAGES=13 \
STRUAI_REVIEW_WAIT=1 node scripts/reviews_workflow.mjs
```
