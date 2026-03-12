# Page 12 Cookbook (Python + JS)

This cookbook shows end-to-end DocQuery traversal on structural page 12, including `cypher` and server-side `crop`.

## Runnable Script (Python)

```bash
export STRUAI_API_KEY=YOUR_API_KEY
export STRUAI_BASE_URL=https://api.stru.ai
python3 examples/page12_cookbook.py
```

## Target Context

- PDF: `structural-compiled.pdf` (96-page structural drawing set)
- Page: `12`
- Typical project used in QC: `proj_86c0f02e`
- Typical sheet on page 12: `S111`

## Install

```bash
pip install struai
npm install struai
```

## Environment

```bash
export STRUAI_API_KEY=YOUR_API_KEY
export STRUAI_BASE_URL=https://api.stru.ai
```

## Python: All 10 Operations

```python
import os
from pathlib import Path
from struai import StruAI

client = StruAI(
    api_key=os.environ["STRUAI_API_KEY"],
    base_url=os.environ.get("STRUAI_BASE_URL", "https://api.stru.ai"),
)
project = client.projects.open("proj_86c0f02e")
sheet_id = "S111"

# 1) project-list
projects = client.projects.list()
print("project_count:", len(projects))

# 2) sheet-list
sheet_list = project.docquery.sheet_list()
print("sheet_nodes:", len(sheet_list.sheet_nodes))

# 3) sheet-summary
sheet_summary = project.docquery.sheet_summary(sheet_id, orphan_limit=10)
print("unreachable:", sheet_summary.reachability.get("unreachable_non_sheet", 0))

# 4) sheet-entities
entities = project.docquery.sheet_entities(sheet_id, limit=20)
print("entities_count:", len(entities.entities))

# 5) search
search = project.docquery.search("section S311", limit=5)
print("search_count:", len(search.hits))

# 6) cypher (custom query string + params)
cypher = project.docquery.cypher(
    "MATCH (n:Entity {project_id:$project_id, sheet_id:$sheet_id}) "
    "WHERE n.bbox_min IS NOT NULL AND n.bbox_max IS NOT NULL "
    "RETURN n.uuid AS uuid, n.page_hash AS page_hash LIMIT 1",
    params={"sheet_id": sheet_id},
    max_rows=1,
)
print("cypher_rows:", len(cypher.records))

if not cypher.records:
    raise RuntimeError("No bbox-capable node found for this sheet")

node_uuid = str(cypher.records[0]["uuid"])

# 7) node-get
node = project.docquery.node_get(node_uuid)
print("node_found:", node.found, "uuid:", node_uuid)

# 8) neighbors
neighbors = project.docquery.neighbors(node_uuid, mode="both", direction="both", radius=200.0, limit=10)
print("neighbors_count:", len(neighbors.neighbors))

# 9) reference-resolve
resolved = project.docquery.reference_resolve(node_uuid, limit=20)
print("reference_count:", resolved.count, "warnings:", len(resolved.warnings))

# 10) crop (uuid mode)
crop_uuid = project.docquery.crop(
    uuid=node_uuid,
    output="/tmp/page12_crop_from_uuid.png",
)
print("crop_uuid:", crop_uuid.output_path, crop_uuid.bytes_written, crop_uuid.content_type)

# Optional: crop (bbox mode)
crop_bbox = project.docquery.crop(
    bbox=[1000, 700, 1400, 980],
    page_hash="66b98c7019417252",
    output="/tmp/page12_crop_from_bbox.png",
)
print("crop_bbox:", crop_bbox.output_path, crop_bbox.bytes_written, crop_bbox.content_type)
```

## JavaScript: Core Traversal + Cypher + Crop

```js
import { StruAI } from "struai";

const apiKey = process.env.STRUAI_API_KEY;
if (!apiKey) throw new Error("Set STRUAI_API_KEY");

const client = new StruAI({
  apiKey,
  baseUrl: process.env.STRUAI_BASE_URL || "https://api.stru.ai",
});

const project = client.projects.open("proj_86c0f02e");
const sheetId = "S111";

const projects = await client.projects.list();
console.log("project_count:", projects.length);

const summary = await project.docquery.sheetSummary(sheetId, { orphanLimit: 10 });
console.log("unreachable:", summary.reachability.unreachable_non_sheet ?? 0);

const cypher = await project.docquery.cypher(
  "MATCH (n:Entity {project_id:$project_id, sheet_id:$sheet_id}) " +
    "WHERE n.bbox_min IS NOT NULL AND n.bbox_max IS NOT NULL " +
    "RETURN n.uuid AS uuid LIMIT 1",
  { params: { sheet_id: sheetId }, maxRows: 1 },
);

const uuid = String(cypher.records[0].uuid);
const crop = await project.docquery.crop({
  uuid,
  output: "/tmp/page12_crop_js.png",
});

console.log("crop:", crop.output_path, crop.bytes_written, crop.content_type);
```

## Notes

- The SDK default base URL is `https://api.stru.ai`.
- `client.projects.list()` is the SDK equivalent of CLI `project-list`.
- The remaining CLI-equivalent operations are under `project.docquery.*`.
