# Reviews Quickstart

Use this when you want to start a review from the SDK and verify that the review lifecycle works end to end.

## Python

Create a review from an existing `file_hash` and refresh it once:

```bash
export STRUAI_API_KEY=your_api_key
export STRUAI_BASE_URL=https://api.stru.ai
export STRUAI_REVIEW_FILE_HASH=your_file_hash
export STRUAI_REVIEW_PAGES=13
export STRUAI_REVIEW_PROJECT_IDS=your_project_id

python3 examples/review_workflow.py
```

Wait for terminal status and fetch persisted questions/issues:

```bash
export STRUAI_REVIEW_WAIT=1
python3 examples/review_workflow.py --wait
```

Use the default review team by omitting the custom prompt env vars entirely.

Create a review by uploading a PDF instead:

```bash
export STRUAI_PDF=/absolute/path/to/structural.pdf
unset STRUAI_REVIEW_FILE_HASH
python3 examples/review_workflow.py --pages 13
```

Create a review with a custom scout and custom specialist team:

```bash
export STRUAI_REVIEW_SCOUT_FILE=/absolute/path/to/examples/prompts/page13_review/scout.md
export STRUAI_REVIEW_SPECIALISTS_COMMON_FILE=/absolute/path/to/examples/prompts/page13_review/specialists_common.md
export STRUAI_REVIEW_SPECIALISTS_FILE=/absolute/path/to/examples/prompts/page13_review/specialists.json

python3 examples/review_workflow.py --file-hash your_file_hash --pages 13
```

## JavaScript

Build the SDK first:

```bash
cd js
npm install
npm run build
```

Start a review and refresh it once:

```bash
export STRUAI_API_KEY=your_api_key
export STRUAI_BASE_URL=https://api.stru.ai
export STRUAI_REVIEW_FILE_HASH=your_file_hash
export STRUAI_REVIEW_PAGES=13
export STRUAI_REVIEW_PROJECT_IDS=your_project_id

node scripts/reviews_workflow.mjs
```

Wait for terminal status:

```bash
export STRUAI_REVIEW_WAIT=1
node scripts/reviews_workflow.mjs
```

Run the same workflow with a custom scout and specialist team:

```bash
export STRUAI_REVIEW_SCOUT_FILE=/absolute/path/to/examples/prompts/page13_review/scout.md
export STRUAI_REVIEW_SPECIALISTS_COMMON_FILE=/absolute/path/to/examples/prompts/page13_review/specialists_common.md
export STRUAI_REVIEW_SPECIALISTS_FILE=/absolute/path/to/examples/prompts/page13_review/specialists.json

node scripts/reviews_workflow.mjs
```

## Quick Checks

- `review_id` should be returned immediately from `create`
- `refresh` should show `status=running` and a `progress` object
- once terminal, `questions()` and `issues()` should return persisted rows
- if the review reaches `failed`, the SDK wait helpers should raise/reject
