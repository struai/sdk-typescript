# Page 13 Review Cookbook

This cookbook runs a full page-13 review against a Stru server using only the Python SDK.

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

## Run

From the SDK repo root:

```bash
python examples/page13_review_cookbook.py
```

## What It Proves

The script uses the Python SDK to:

1. create a review on page 13
2. check status repeatedly while it runs
3. fetch questions and issues as they appear
4. collect elapsed-time and turn-count stats
5. reopen the finished review and fetch historical results again

## Expected Target

- file hash: `168459a574292229`
- project id: `proj_86c0f02e`
- page selector: `13`
