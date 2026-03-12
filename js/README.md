# StruAI JavaScript SDK

Official JavaScript/TypeScript SDK for the StruAI Drawing Analysis API.

## Installation

```bash
npm install struai
```

## Environment

```bash
export STRUAI_API_KEY=your_api_key
# Optional: defaults to https://api.stru.ai (SDK appends /v1 automatically)
export STRUAI_BASE_URL=https://api.stru.ai
```

## Quick Start

```ts
import { StruAI } from 'struai';

const client = new StruAI({
  apiKey: process.env.STRUAI_API_KEY!,
  baseUrl: process.env.STRUAI_BASE_URL, // optional
  timeout: 60_000, // optional
});

const drawing = await client.drawings.analyze('/absolute/path/to/structural.pdf', { page: 12 });
const project = await client.projects.create({ name: 'Building A', description: 'Structural set' });
const jobOrBatch = await project.sheets.add(null, {
  page: 12,
  fileHash: await client.drawings.computeFileHash('/absolute/path/to/structural.pdf'),
});

const search = await project.docquery.search('beam connection', { limit: 5 });
console.log(search.hits.length);

const review = await client.reviews.create({
  fileHash: await client.drawings.computeFileHash('/absolute/path/to/structural.pdf'),
  pages: '12,13',
  projectIds: [project.id],
  customInstructions: 'Focus on cross-sheet coordination.',
});
const finalReview = await review.wait({ timeoutMs: 900_000, pollIntervalMs: 5_000 });
console.log(finalReview.status, (await review.issues()).length);

const uploadReview = await client.reviews.create({
  file: '/absolute/path/to/structural.pdf',
  pages: 12,
});
console.log(uploadReview.id);
```

## Real Workflow Examples

```bash
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

# Optional cleanup after full workflow
STRUAI_CLEANUP=1 node scripts/projects_workflow.mjs

# Review workflow (start + refresh)
STRUAI_API_KEY=... STRUAI_BASE_URL=https://api.stru.ai \
STRUAI_REVIEW_FILE_HASH=your_file_hash STRUAI_REVIEW_PAGES=13 \
node scripts/reviews_workflow.mjs

# Review workflow (wait for terminal status)
STRUAI_API_KEY=... STRUAI_BASE_URL=https://api.stru.ai \
STRUAI_REVIEW_FILE_HASH=your_file_hash STRUAI_REVIEW_PAGES=13 STRUAI_REVIEW_WAIT=1 \
node scripts/reviews_workflow.mjs
```

See `scripts/README.md` for quick copy/paste commands.

## API Reference

### Client

- `new StruAI({ apiKey, baseUrl?, timeout? })`
- `client.drawings`
- `client.projects`
- `client.reviews`

### Drawings (`client.drawings`)

- `analyze(file, { page, fileHash? }) -> Promise<DrawingResult>`
  - Pass either `file` or `fileHash`.
  - `file` can be a file path string, `Blob`, `ArrayBuffer`, or typed array.
- `checkCache(fileHash) -> Promise<DrawingCacheStatus>`
- `computeFileHash(file) -> Promise<string>`

### Projects Top-Level (`client.projects`)

- `create({ name, description? }) -> Promise<ProjectInstance>`
- `list() -> Promise<Project[]>`
- `open(projectId, { name?, description? }?) -> ProjectInstance`
- `delete(projectId) -> Promise<ProjectDeleteResult>`

### Reviews Top-Level (`client.reviews`)

- `create({ file?, pages, fileHash?, projectIds?, customInstructions? }) -> Promise<ReviewInstance>`
  - Pass exactly one of `file` or `fileHash`.
  - Throws if both are missing or both are provided.
- `list({ status? }?) -> Promise<Review[]>`
- `get(reviewId) -> Promise<ReviewInstance>`
- `open(reviewId) -> ReviewInstance`

### Project Instance (`project`)

Properties:

- `id`, `name`, `description`, `data`
- `sheets`, `docquery`

Methods:

- `delete() -> Promise<ProjectDeleteResult>`

### Review Instance (`review`)

Properties:

- `id`, `data`

Methods:

- `refresh() -> Promise<Review>`
- `status() -> Promise<Review>`
- `wait({ timeoutMs?, pollIntervalMs? }?) -> Promise<Review>`
  - Rejects if the review reaches `failed`.
  - Rejects if the timeout elapses first.
- `questions() -> Promise<ReviewQuestion[]>`
- `issues() -> Promise<ReviewIssue[]>`

### Sheets (`project.sheets`)

- `add(file, { page, fileHash?, sourceDescription?, onSheetExists?, communityUpdateMode?, semanticIndexUpdateMode? }) -> Promise<Job | JobBatch>`
  - `page` supports `12`, `'1,3,5-7'`, `'all'`
  - Pass either `file` or `fileHash`
- `delete(sheetId) -> Promise<SheetDeleteResult>`
- `job(jobId, { page? }?) -> Job`

### DocQuery (`project.docquery`)

- `nodeGet(uuid) -> Promise<DocQueryNodeGetResult>`
- `sheetEntities(sheetId, { entityType?, limit? }?) -> Promise<DocQuerySheetEntitiesResult>`
- `search(query, { index?, limit? }?) -> Promise<DocQuerySearchResult>`
- `neighbors(uuid, { mode?, direction?, relationshipType?, radius?, limit? }?) -> Promise<DocQueryNeighborsResult>`
- `cypher(query, { params?, maxRows? }?) -> Promise<DocQueryCypherResult>`
- `sheetSummary(sheetId, { orphanLimit? }?) -> Promise<DocQuerySheetSummaryResult>`
- `sheetList() -> Promise<DocQuerySheetListResult>`
- `referenceResolve(uuid, { limit? }?) -> Promise<DocQueryReferenceResolveResult>`
- `crop({ output, uuid?, bbox?, pageHash? }) -> Promise<DocQueryCropResult>`

CLI parity: `project-list` maps to `client.projects.list()`, and the remaining 9 commands map to `project.docquery.*`, for full 10-command parity.

```ts
const project = client.projects.open('proj_86c0f02e');
const cypher = await project.docquery.cypher(
  'MATCH (n:Entity {project_id:$project_id}) RETURN count(n) AS total',
  { params: {}, maxRows: 1 }
);
const crop = await project.docquery.crop({
  uuid: 'entity-uuid-here',
  output: '/absolute/path/to/crop.png',
});
console.log(cypher.records[0]?.total, crop.output_path, crop.bytes_written);
```

### Jobs

`Job`:

- `id`, `page`
- `status() -> Promise<JobStatus>`
- `wait({ timeoutMs?, pollIntervalMs? }?) -> Promise<SheetResult>`

`JobBatch`:

- `jobs`, `ids`
- `statusAll() -> Promise<JobStatus[]>`
- `waitAll({ timeoutMs?, pollIntervalMs? }?) -> Promise<SheetResult[]>`

### Reviews

`Review`:

- `review_id`, `status`, `total_pages`, `pages`, `progress`
- `is_running`, `is_complete`, `is_partial`, `is_failed`, `is_terminal`
- Status values: `running`, `completed`, `completed_partial`, `failed`
- `pages` and `total_pages` are populated by `POST /v1/reviews`; later `refresh()` / `get()` calls reflect the slimmer `GET /v1/reviews/{review_id}` payload and may omit them.
- `progress.specialist.active` contains live in-progress specialist rows with `question_id`, `agent`, `turns_used`, `max_turns`, and `updated_at` when the server exposes them.

`ReviewQuestion`:

- Includes `raw_model_output`, preserved as nested JSON when present.

## Endpoint Coverage

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
- `POST /v1/reviews`
- `GET /v1/reviews`
- `GET /v1/reviews/{review_id}`
- `GET /v1/reviews/{review_id}/questions`
- `GET /v1/reviews/{review_id}/issues`

## License

MIT
