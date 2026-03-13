# StruAI SDK (Python + JavaScript)

Official SDKs for the StruAI Drawing Analysis API.

- Python package: `struai` (PyPI)
- JavaScript package: `struai` (npm, source in `js/`)
- Endpoint + response-shape reference: `docs/HTTP_ENDPOINTS.md`

## Install

```bash
pip install struai
npm install struai
```

## Environment

```bash
export STRUAI_API_KEY=your_api_key
# Optional: defaults to https://api.stru.ai (SDK appends /v1 automatically)
export STRUAI_BASE_URL=https://api.stru.ai
```

## Python Quick Start

```python
import os
from struai import StruAI

client = StruAI(api_key=os.environ["STRUAI_API_KEY"])

# Tier 1: drawings
result = client.drawings.analyze("structural.pdf", page=12)
print(result.id, result.processing_ms)

# Tier 2: projects + docquery
project = client.projects.create(name="Building A", description="Structural set")
job = project.sheets.add(page=12, file_hash=client.drawings.compute_file_hash("structural.pdf"))
sheet = job.wait(timeout=180)

hits = project.docquery.search("beam connection", limit=5)
print(len(hits.hits))

# Tier 3: reviews (default review team)
review = client.reviews.create(
    file_hash=client.drawings.compute_file_hash("structural.pdf"),
    pages="12,13",
    project_ids=[project.id],
    custom_instructions="Focus on cross-sheet coordination.",
)
final_review = review.wait(timeout=900, poll_interval=5)
print(final_review.status, len(review.issues()))

# Tier 3: reviews (custom scout + custom specialist team)
custom_review = client.reviews.create(
    file_hash=client.drawings.compute_file_hash("structural.pdf"),
    pages="13",
    project_ids=[project.id],
    scout="Look broadly for issues worth deeper investigation.",
    specialists_common="All specialists should stay grounded in DocQuery/search-docs evidence.",
    specialists=[
        {"name": "Cross Reference Checker", "instructions": "Trace all detail, section, and sheet references."},
        {"name": "Constructability Reviewer", "instructions": "Focus on missing dimensions and buildability gaps."},
    ],
)
print(custom_review.id)

# Direct upload path also works
upload_review = client.reviews.create(
    file="structural.pdf",
    pages=12,
)
print(upload_review.id)
```

## Real Workflow Examples

Python examples (`/examples`):

```bash
# Drawings-only flow (hash, cache probe, analyze)
python3 examples/test_prod_page12.py --pdf /absolute/path/to/structural.pdf --page 12

# Full projects + docquery workflow
python3 examples/test_prod_page12_full.py --pdf /absolute/path/to/structural.pdf --page 12

# Full workflow + crop demo
python3 examples/test_prod_page12_full.py \
  --pdf /absolute/path/to/structural.pdf --page 12 \
  --crop-output /absolute/path/to/crop.png

# Optional cleanup after full workflow
python3 examples/test_prod_page12_full.py --pdf /absolute/path/to/structural.pdf --cleanup

# Async workflow
python3 examples/async_projects_workflow.py --pdf /absolute/path/to/structural.pdf --page 12

# Review workflow (start + refresh)
python3 examples/review_workflow.py --file-hash your_file_hash --pages 13

# Review workflow (wait for terminal status)
python3 examples/review_workflow.py --file-hash your_file_hash --pages 13 --wait

# Page-13 review cookbook (default review team)
python3 examples/page13_review_cookbook.py

# Page-13 review cookbook (custom scout + custom specialist team)
STRUAI_REVIEW_SCOUT_FILE=/absolute/path/to/examples/prompts/page13_review/scout.md \
STRUAI_REVIEW_SPECIALISTS_COMMON_FILE=/absolute/path/to/examples/prompts/page13_review/specialists_common.md \
STRUAI_REVIEW_SPECIALISTS_FILE=/absolute/path/to/examples/prompts/page13_review/specialists.json \
python3 examples/page13_review_cookbook.py
```

Page-12 cookbook with all 10 operations (including `cypher` and `crop`):
- `examples/PAGE12_COOKBOOK.md`
- `examples/prompts/page13_review/README.md`
- `examples/REVIEWS_QUICKSTART.md`

JavaScript examples (`/js/scripts`):

```bash
cd js
npm install
npm run build

# Drawings-only flow
STRUAI_API_KEY=... STRUAI_BASE_URL=https://api.stru.ai \
STRUAI_PDF=/absolute/path/to/structural.pdf STRUAI_PAGE=12 \
node scripts/drawings_quickstart.mjs

# Full projects + docquery workflow
STRUAI_API_KEY=... STRUAI_BASE_URL=https://api.stru.ai \
STRUAI_PDF=/absolute/path/to/structural.pdf STRUAI_PAGE=12 \
node scripts/projects_workflow.mjs

# Full workflow + crop demo
STRUAI_API_KEY=... STRUAI_BASE_URL=https://api.stru.ai \
STRUAI_PDF=/absolute/path/to/structural.pdf STRUAI_PAGE=12 \
STRUAI_CROP_OUTPUT=/absolute/path/to/crop.png \
node scripts/projects_workflow.mjs

# Review workflow (default review team)
STRUAI_API_KEY=... STRUAI_BASE_URL=https://api.stru.ai \
STRUAI_REVIEW_FILE_HASH=your_file_hash STRUAI_REVIEW_PAGES=13 \
node scripts/reviews_workflow.mjs

# Review workflow (custom scout + custom specialist team)
STRUAI_API_KEY=... STRUAI_BASE_URL=https://api.stru.ai \
STRUAI_REVIEW_FILE_HASH=your_file_hash STRUAI_REVIEW_PAGES=13 \
STRUAI_REVIEW_SCOUT_FILE=/absolute/path/to/examples/prompts/page13_review/scout.md \
STRUAI_REVIEW_SPECIALISTS_COMMON_FILE=/absolute/path/to/examples/prompts/page13_review/specialists_common.md \
STRUAI_REVIEW_SPECIALISTS_FILE=/absolute/path/to/examples/prompts/page13_review/specialists.json \
node scripts/reviews_workflow.mjs
```

## Python API Reference

Async API (`AsyncStruAI`) mirrors the same resource shape and method names; use `await`.

### Client

- `StruAI(api_key=None, base_url="https://api.stru.ai", timeout=60, max_retries=2)`
- `AsyncStruAI(api_key=None, base_url="https://api.stru.ai", timeout=60, max_retries=2)`
- `client.drawings`
- `client.projects`
- `client.reviews`

### Drawings (`client.drawings`)

- `analyze(file=None, page=1, file_hash=None) -> DrawingResult`
- `check_cache(file_hash) -> DrawingCacheStatus`
- `compute_file_hash(file) -> str`

### Projects Top-Level (`client.projects`)

- `create(name, description=None) -> ProjectInstance`
- `list() -> list[Project]`
- `open(project_id, name=None, description=None) -> ProjectInstance`
- `delete(project_id) -> ProjectDeleteResult`

### Reviews Top-Level (`client.reviews`)

- `create(file=None, pages=1|"1,3,5-7"|"all", file_hash=None, project_ids=None, scout=None, specialists_common=None, specialists=None, custom_instructions=None) -> ReviewInstance`
  - Pass exactly one of `file` or `file_hash`.
  - Raises `ValueError` if both are missing or both are provided.
  - `specialists` must be a non-empty list of `{name, instructions}` objects when provided.
  - Omit `scout`, `specialists_common`, and `specialists` to use the default review team.
- `list(status=None) -> list[Review]`
- `get(review_id) -> ReviewInstance`
- `open(review_id) -> ReviewInstance`

### Project Instance (`project`)

Properties:

- `id`, `name`, `description`, `data`
- `sheets`, `docquery`

Methods:

- `delete() -> ProjectDeleteResult`

### Review Instance (`review`)

Properties:

- `id`, `data`

Methods:

- `refresh() -> Review`
- `status() -> Review`
- `wait(timeout=900, poll_interval=5) -> Review`
  - Raises `ReviewFailedError` if the review reaches `failed`.
  - Raises `TimeoutError` if the timeout elapses first.
- `questions() -> list[ReviewQuestion]`
- `issues() -> list[ReviewIssue]`

### Sheets (`project.sheets`)

- `add(file=None, page=1|"1,3,5-7"|"all", file_hash=None, source_description=None, on_sheet_exists=None, community_update_mode=None, semantic_index_update_mode=None) -> Job | JobBatch`
- `delete(sheet_id) -> SheetDeleteResult`
- `job(job_id, page=None) -> Job`

### DocQuery (`project.docquery`)

- `node_get(uuid) -> DocQueryNodeGetResult`
- `sheet_entities(sheet_id, entity_type=None, limit=200) -> DocQuerySheetEntitiesResult`
- `search(query, index="entity_search", limit=20) -> DocQuerySearchResult`
- `neighbors(uuid, mode="both", direction="both", relationship_type=None, radius=200.0, limit=50) -> DocQueryNeighborsResult`
- `cypher(query, params=None, max_rows=500) -> DocQueryCypherResult`
- `sheet_summary(sheet_id, orphan_limit=10) -> DocQuerySheetSummaryResult`
- `sheet_list() -> DocQuerySheetListResult`
- `reference_resolve(uuid, limit=100) -> DocQueryReferenceResolveResult`
- `crop(output, uuid=None, bbox=None, page_hash=None) -> DocQueryCropResult`

CLI parity: `project-list` maps to `client.projects.list()`, and the remaining 9 commands map to `project.docquery.*`, for full 10-command parity.

Python cypher + crop example:

```python
project = client.projects.open("proj_86c0f02e")
rows = project.docquery.cypher(
    "MATCH (n:Entity {project_id:$project_id}) RETURN count(n) AS total",
    params={},
    max_rows=1,
)

crop = project.docquery.crop(
    uuid="entity-uuid-here",
    output="/absolute/path/to/crop.png",
)
print(rows.records[0]["total"], crop.output_path, crop.bytes_written)
```

### Jobs

`Job` (single-page ingest result):

- `id`, `page`
- `status() -> JobStatus`
- `wait(timeout=120, poll_interval=2) -> SheetResult`

`JobBatch` (multi-page ingest result):

- `jobs`, `ids`
- `status_all() -> list[JobStatus]`
- `wait_all(timeout_per_job=120, poll_interval=2) -> list[SheetResult]`

### Reviews

`Review`:

- `review_id`, `status`, `total_pages`, `pages`, `progress`
- `is_running`, `is_complete`, `is_partial`, `is_failed`, `is_terminal`
- Status values: `running`, `completed`, `completed_partial`, `failed`
- `pages` and `total_pages` are populated by `POST /v1/reviews`; later `refresh()` / `get()` calls reflect the slimmer `GET /v1/reviews/{review_id}` payload and may omit them.
- `progress.specialist.active` contains live in-progress specialist rows with `question_id`, `agent`, `turns_used`, `max_turns`, and `updated_at` when the server exposes them.

`ReviewQuestion`:

- Includes `raw_model_output`, which is preserved as nested JSON when present.

## HTTP Endpoints Covered

Full endpoint + response-shape reference: `docs/HTTP_ENDPOINTS.md`

Tier 1:

- `POST /v1/drawings`
- `GET /v1/drawings/cache/{file_hash}`

Tier 2:

- `POST /v1/projects`
- `GET /v1/projects`
- `DELETE /v1/projects/{project_id}`
- `POST /v1/projects/{project_id}/sheets`
- `DELETE /v1/projects/{project_id}/sheets/{sheet_id}`
- `GET /v1/projects/{project_id}/jobs/{job_id}`
- `GET /v1/projects/{project_id}/node-get`
- `GET /v1/projects/{project_id}/sheet-entities`
- `GET /v1/projects/{project_id}/search`
- `GET /v1/projects/{project_id}/neighbors`
- `POST /v1/projects/{project_id}/cypher`
- `POST /v1/projects/{project_id}/crop`

Tier 3:

- `POST /v1/reviews`
- `GET /v1/reviews`
- `GET /v1/reviews/{review_id}`
- `GET /v1/reviews/{review_id}/questions`
- `GET /v1/reviews/{review_id}/issues`

## JavaScript Reference

See `js/README.md` for complete JS method signatures and usage patterns.

## License

MIT
