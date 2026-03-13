# Page 13 Review Cookbook

This cookbook runs a full page-13 review against a Stru server using only the Python SDK.

It supports two modes:

1. default review team: use the server defaults, only pass `file_hash`, `pages`, and optional `project_ids`
2. custom review team: pass `scout`, `specialists_common`, and `specialists` from prompt files

## Environment

Set the following environment variables (or create a `.env` file in the repo root):

```bash
STRUAI_API_KEY=your_api_key
STRUAI_REVIEW_FILE_HASH=168459a574292229
STRUAI_REVIEW_PAGES=13
STRUAI_REVIEW_PROJECT_IDS=proj_86c0f02e
STRUAI_REVIEW_TIMEOUT=2100
STRUAI_REVIEW_POLL_INTERVAL=10
```

For local development, also set:

```bash
STRUAI_BASE_URL=http://localhost:8000
```

If `STRUAI_BASE_URL` is not set, the SDK defaults to `https://api.stru.ai`.

## Custom Review-Team Mode

To run the same cookbook with a custom scout and custom specialist team, also set:

```bash
STRUAI_REVIEW_SCOUT_FILE=/absolute/path/to/examples/prompts/page13_review/scout.md
STRUAI_REVIEW_SPECIALISTS_COMMON_FILE=/absolute/path/to/examples/prompts/page13_review/specialists_common.md
STRUAI_REVIEW_SPECIALISTS_FILE=/absolute/path/to/examples/prompts/page13_review/specialists.json
```

Sample prompt assets live in:

- `examples/prompts/page13_review/scout.md`
- `examples/prompts/page13_review/specialists_common.md`
- `examples/prompts/page13_review/specialists.json`
- `examples/prompts/page13_review/README.md`

Important:

- when you supply `specialists.json`, the scout text must mention each specialist by exact name
- the server validates this before the review starts

## Run

From the SDK repo root:

```bash
# Default review team
python examples/page13_review_cookbook.py

# Custom scout + custom specialist team
STRUAI_REVIEW_SCOUT_FILE=/absolute/path/to/examples/prompts/page13_review/scout.md \
STRUAI_REVIEW_SPECIALISTS_COMMON_FILE=/absolute/path/to/examples/prompts/page13_review/specialists_common.md \
STRUAI_REVIEW_SPECIALISTS_FILE=/absolute/path/to/examples/prompts/page13_review/specialists.json \
python examples/page13_review_cookbook.py
```

## What It Proves

The script uses the Python SDK to:

1. create a review on page 13
2. optionally create that review with a custom scout and custom specialist team
3. check status repeatedly while it runs
4. fetch questions and issues as they appear
5. collect elapsed-time and turn-count stats
6. reopen the finished review and fetch historical results again

## Expected Target

- file hash: `168459a574292229`
- project id: `proj_86c0f02e`
- page selector: `13`
