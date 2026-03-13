# StruAI HTTP Endpoints and Response Shapes

Quick reference for the production API behind the SDK.

- Production base URL: `https://api.stru.ai`
- Versioned API root: `https://api.stru.ai/v1`
- The SDKs accept `base_url="https://api.stru.ai"` and append `/v1` automatically.

This document is intentionally endpoint-first: what to call, and what shape comes back.

## Tier 1: Drawings

### `POST /v1/drawings`

- SDK: `client.drawings.analyze(...)`
- Response model: `DrawingResult`

```json
{
  "id": "drw_...",
  "page": 12,
  "dimensions": { "width": 3168, "height": 2448 },
  "processing_ms": 1842,
  "annotations": {
    "leaders": [],
    "section_tags": [],
    "detail_tags": [],
    "revision_triangles": [],
    "revision_clouds": []
  },
  "titleblock": {
    "bounds": [0, 0, 0, 0],
    "viewport": [0, 0, 0, 0]
  }
}
```

### `GET /v1/drawings/cache/{file_hash}`

- SDK: `client.drawings.check_cache(file_hash)`
- Response model: `DrawingCacheStatus`

```json
{
  "cached": true,
  "file_hash": "168459a574292229"
}
```

## Tier 2: Projects, Jobs, and DocQuery

### `POST /v1/projects`

- SDK: `client.projects.create(name=..., description=...)`
- Response model: `Project`

```json
{
  "id": "proj_86c0f02e",
  "name": "Building A",
  "description": "Structural set",
  "created_at": "2026-03-07T10:00:00Z"
}
```

### `GET /v1/projects`

- SDK: `client.projects.list()`
- Response model: `ProjectListResponse`

```json
{
  "projects": [
    {
      "id": "proj_86c0f02e",
      "name": "Building A",
      "description": "Structural set",
      "created_at": "2026-03-07T10:00:00Z"
    }
  ]
}
```

### `DELETE /v1/projects/{project_id}`

- SDK: `client.projects.delete(project_id)` or `project.delete()`
- Response model: `ProjectDeleteResult`

```json
{
  "deleted": true,
  "project_id": "proj_86c0f02e",
  "projects_deleted": 1,
  "nodes_deleted": 248,
  "relationships_deleted": 511,
  "owner_mapping_deleted": true,
  "qdrant_deleted_points": 972
}
```

### `POST /v1/projects/{project_id}/sheets`

- SDK: `project.sheets.add(...)`
- Response model: `SheetIngestResponse`

```json
{
  "jobs": [
    { "job_id": "job_a4de1b2661", "page": 13 }
  ]
}
```

### `DELETE /v1/projects/{project_id}/sheets/{sheet_id}`

- SDK: `project.sheets.delete(sheet_id)`
- Response model: `SheetDeleteResult`

```json
{
  "deleted": true,
  "project_id": "proj_86c0f02e",
  "sheet_id": "S112",
  "nodes_deleted": 88,
  "relationships_deleted_by_source_sheet": 144,
  "qdrant": {
    "deleted_points": 193
  }
}
```

### `GET /v1/projects/{project_id}/jobs/{job_id}`

- SDK: `job.status()` or `project.sheets.job(job_id).status()`
- Response model: `JobStatus`

```json
{
  "job_id": "job_a4de1b2661",
  "page": 13,
  "status": "complete",
  "created_at_utc": "2026-03-07T10:00:00Z",
  "started_at_utc": "2026-03-07T10:00:01Z",
  "completed_at_utc": "2026-03-07T10:06:14Z",
  "current_step": "step_5_qdrant_indexing",
  "step_timings": {
    "step_2c_merge": {
      "start_utc": "2026-03-07T10:01:12Z",
      "end_utc": "2026-03-07T10:06:08Z",
      "duration_ms": 296285
    }
  },
  "status_log": [],
  "result": {
    "sheet_id": "S112",
    "entities_created": 88,
    "relationships_created": 144,
    "skipped": false
  },
  "error": null
}
```

### `GET /v1/projects/{project_id}/node-get`

- SDK: `project.docquery.node_get(uuid)`
- Response model: `DocQueryNodeGetResult`

```json
{
  "ok": true,
  "found": true,
  "node": {
    "uuid": "entity-uuid",
    "type": "Detail",
    "sheet_id": "S112"
  }
}
```

### `GET /v1/projects/{project_id}/sheet-entities`

- SDK: `project.docquery.sheet_entities(sheet_id, entity_type=None, limit=200)`
- Response model: `DocQuerySheetEntitiesResult`

```json
{
  "ok": true,
  "entities": [
    {
      "uuid": "entity-uuid",
      "type": "Section",
      "sheet_id": "S112"
    }
  ]
}
```

### `GET /v1/projects/{project_id}/search`

- SDK: `project.docquery.search(query, index="entity_search", limit=20)`
- Response model: `DocQuerySearchResult`

```json
{
  "ok": true,
  "hits": [
    {
      "node": {
        "uuid": "entity-uuid",
        "text": "beam connection"
      },
      "score": 0.88
    }
  ]
}
```

### `GET /v1/projects/{project_id}/neighbors`

- SDK: `project.docquery.neighbors(uuid, ...)`
- Response model: `DocQueryNeighborsResult`

```json
{
  "ok": true,
  "mode": "both",
  "neighbors": [
    {
      "direction": "outgoing",
      "relationship": { "type": "REFERENCES" },
      "neighbor": { "uuid": "neighbor-uuid" },
      "distance_px": 64.0,
      "linked": true,
      "edges": []
    }
  ]
}
```

### `POST /v1/projects/{project_id}/cypher`

- SDK: `project.docquery.cypher(query, params=None, max_rows=500)`
- Response model: `DocQueryCypherResult`

```json
{
  "ok": true,
  "records": [
    { "total": 248 }
  ],
  "truncated": false
}
```

### `GET /v1/projects/{project_id}/sheet-summary`

- SDK: `project.docquery.sheet_summary(sheet_id, orphan_limit=10)`
- Response model: `DocQuerySheetSummaryResult`

```json
{
  "ok": true,
  "command": "sheet-summary",
  "input": { "sheet_id": "S112" },
  "sheet_node": {},
  "node_label_counts": [],
  "relationship_counts": [],
  "reachability": {},
  "orphan_examples": [],
  "warnings": []
}
```

### `GET /v1/projects/{project_id}/sheet-list`

- SDK: `project.docquery.sheet_list()`
- Response model: `DocQuerySheetListResult`

```json
{
  "ok": true,
  "command": "sheet-list",
  "input": {},
  "sheet_nodes": [],
  "entity_sheet_inventory": [],
  "totals": {},
  "mismatch_warnings": []
}
```

### `GET /v1/projects/{project_id}/reference-resolve`

- SDK: `project.docquery.reference_resolve(uuid, limit=100)`
- Response model: `DocQueryReferenceResolveResult`

```json
{
  "ok": true,
  "command": "reference-resolve",
  "input": { "uuid": "entity-uuid" },
  "found": true,
  "source": {},
  "resolved_references": [],
  "count": 0,
  "warnings": []
}
```

### `POST /v1/projects/{project_id}/crop`

- SDK: `project.docquery.crop(output=..., uuid=... | bbox=... | page_hash=...)`
- Response model: `DocQueryCropResult`

```json
{
  "ok": true,
  "output_path": "/absolute/path/to/crop.png",
  "bytes_written": 182933,
  "content_type": "image/png"
}
```

## Tier 3: Reviews

### `POST /v1/reviews`

- SDK: `client.reviews.create(...)`
- Response model: `Review`

Request supports two review modes:

- default review team: omit `scout`, `specialists_common`, and `specialists`
- custom review team: supply any or all of those fields

```json
{
  "review_id": "rev_a1b2c3d4e5f6",
  "status": "running",
  "total_pages": 1,
  "pages": [
    {
      "page_number": 13,
      "page_hash": "83e1145e4253f6bc",
      "project_id": "proj_86c0f02e"
    }
  ]
}
```

### `GET /v1/reviews`

- SDK: `client.reviews.list(status=None)`
- Response model: `ReviewListResponse`

```json
{
  "reviews": [
    {
      "review_id": "rev_a1b2c3d4e5f6",
      "status": "completed",
      "owner_user_id": "102170351054403182161",
      "file_hash": "168459a574292229",
      "page_selector": "13",
      "requested_project_ids": ["proj_86c0f02e"],
      "custom_instructions": null,
      "created_at": "2026-03-07T10:00:00Z",
      "completed_at": "2026-03-07T10:15:00Z"
    }
  ]
}
```

### `GET /v1/reviews/{review_id}`

- SDK: `client.reviews.get(review_id)` or `review.refresh()`
- Response model: `Review`

```json
{
  "review_id": "rev_a1b2c3d4e5f6",
  "status": "running",
  "created_at": "2026-03-07T10:00:00Z",
  "completed_at": null,
  "file_hash": "168459a574292229",
  "custom_instructions": null,
  "progress": {
    "scout": {
      "pending": 0,
      "in_progress": 0,
      "completed": 1,
      "failed": 0,
      "total": 1
    },
    "specialist": {
      "pending": 1,
      "in_progress": 2,
      "completed": 4,
      "failed": 0,
      "out_of_scope": 0,
      "total": 7,
      "max_turns": 30,
      "active": [
        {
          "question_id": "q_active_1",
          "agent": "Cross Reference Checker",
          "turns_used": 2,
          "max_turns": 30,
          "updated_at": "2026-03-07T10:05:00Z"
        }
      ]
    }
  }
}
```

### `GET /v1/reviews/{review_id}/questions`

- SDK: `review.questions()`
- Response model: `ReviewQuestionsResult`

```json
{
  "review_id": "rev_a1b2c3d4e5f6",
  "questions": [
    {
      "question_id": "q_1",
      "review_id": "rev_a1b2c3d4e5f6",
      "review_page_id": "rp_1",
      "source": "scout",
      "status": "completed",
      "page_hash": "83e1145e4253f6bc",
      "project_id": "proj_86c0f02e",
      "question": "Check the broken detail callout at the north edge.",
      "location_description": "north edge framing note cluster",
      "assigned_agents": ["Cross Reference Checker"],
      "spawned_by_question_id": null,
      "started_at": "2026-03-07T10:01:00Z",
      "completed_at": "2026-03-07T10:02:30Z",
      "turns_used": 4,
      "error": null,
      "raw_model_output": null,
      "created_at": "2026-03-07T10:01:00Z",
      "updated_at": "2026-03-07T10:02:30Z"
    }
  ]
}
```

### `GET /v1/reviews/{review_id}/issues`

- SDK: `review.issues()`
- Response model: `ReviewIssuesResult`

```json
{
  "review_id": "rev_a1b2c3d4e5f6",
  "issues": [
    {
      "issue_id": "iss_1",
      "review_id": "rev_a1b2c3d4e5f6",
      "question_id": "q_1",
      "project_id": "proj_86c0f02e",
      "page_hash": "83e1145e4253f6bc",
      "agent": "Cross Reference Checker",
      "priority": "P1",
      "category": "missing_info",
      "title": "Missing referenced section",
      "description": "Callout references a missing section.",
      "evidence": [
        "Detail callout text reads 4/S312."
      ],
      "suggested_fix": "Correct the callout.",
      "created_at": "2026-03-07T10:05:00Z"
    }
  ]
}
```
