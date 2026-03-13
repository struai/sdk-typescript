/**
 * Full Tier 1 + Tier 2 projects/docquery workflow example.
 *
 * Usage:
 *   npm run build
 *   STRUAI_API_KEY=... \
 *   STRUAI_PDF=/absolute/path/to/structural.pdf STRUAI_PAGE=12 \
 *   node scripts/projects_workflow.mjs
 *
 * Optional cleanup:
 *   STRUAI_CLEANUP=1 node scripts/projects_workflow.mjs
 *
 * Optional crop demo:
 *   STRUAI_CROP_OUTPUT=/tmp/crop.png node scripts/projects_workflow.mjs
 */

import fs from 'node:fs/promises';
import path from 'node:path';
import { StruAI } from '../dist/index.mjs';

const apiKey = process.env.STRUAI_API_KEY;
const baseUrl = process.env.STRUAI_BASE_URL ?? 'https://api.stru.ai';
const pdfPath = process.env.STRUAI_PDF;
const page = Number(process.env.STRUAI_PAGE ?? '12');
const query = process.env.STRUAI_QUERY ?? 'beam connection';
const cleanup = process.env.STRUAI_CLEANUP === '1';
const cropOutput = process.env.STRUAI_CROP_OUTPUT ?? 'sdk_crop_js.png';
const timeoutMs = Number(process.env.STRUAI_TIMEOUT_MS ?? '240000');
const pollIntervalMs = Number(process.env.STRUAI_POLL_INTERVAL_MS ?? '2000');

if (!apiKey) {
  console.error('Missing STRUAI_API_KEY');
  process.exit(1);
}
if (!pdfPath) {
  console.error('Missing STRUAI_PDF');
  process.exit(1);
}

try {
  await fs.access(pdfPath);
} catch {
  console.error(`PDF not found: ${pdfPath}`);
  process.exit(1);
}

const client = new StruAI({ apiKey, baseUrl });

console.log('== Tier 1: Drawings ==');
const fileHash = await client.drawings.computeFileHash(pdfPath);
const cache = await client.drawings.checkCache(fileHash);
console.log(`file_hash=${fileHash} cached=${cache.cached}`);

const drawing = cache.cached
  ? await client.drawings.analyze(null, { page, fileHash })
  : await client.drawings.analyze(pdfPath, { page });
console.log(`drawing_id=${drawing.id} page=${drawing.page} processing_ms=${drawing.processing_ms}`);

console.log('\n== Tier 2: Projects + DocQuery ==');
const project = await client.projects.create({
  name: `JS SDK Workflow ${Date.now()}`,
  description: `Created from ${path.basename(pdfPath)} page ${page}`,
});
console.log(`project_created id=${project.id} name=${project.name}`);

const projects = await client.projects.list();
console.log(`projects_list_count=${projects.length}`);

const openedProject = client.projects.open(project.id);
console.log(`project_open id=${openedProject.id} name=${openedProject.name}`);

const jobOrBatch = cache.cached
  ? await project.sheets.add(null, {
      page,
      fileHash,
      sourceDescription: `${path.basename(pdfPath)} page ${page}`,
      onSheetExists: 'skip',
      communityUpdateMode: 'incremental',
      semanticIndexUpdateMode: 'incremental',
    })
  : await project.sheets.add(pdfPath, {
      page,
      sourceDescription: `${path.basename(pdfPath)} page ${page}`,
      onSheetExists: 'skip',
      communityUpdateMode: 'incremental',
      semanticIndexUpdateMode: 'incremental',
    });

let sheetResult;
if ('waitAll' in jobOrBatch) {
  const statuses = await jobOrBatch.statusAll();
  console.log(`initial_batch_statuses=${statuses.map((s) => `${s.job_id}:${s.status}`).join(',')}`);
  const results = await jobOrBatch.waitAll({ timeoutMs, pollIntervalMs });
  sheetResult = results.find((item) => item.sheet_id) ?? results[0];
} else {
  const status = await jobOrBatch.status();
  console.log(`initial_job_status job_id=${status.job_id} status=${status.status}`);
  sheetResult = await jobOrBatch.wait({ timeoutMs, pollIntervalMs });
}

console.log(
  `sheet_result sheet_id=${sheetResult.sheet_id ?? ''} ` +
    `entities_created=${sheetResult.entities_created ?? 0} ` +
    `relationships_created=${sheetResult.relationships_created ?? 0}`
);

if (sheetResult.sheet_id) {
  const sheetEntities = await project.docquery.sheetEntities(sheetResult.sheet_id, { limit: 20 });
  console.log(`sheet_entities_count=${sheetEntities.entities.length}`);

  const sheetSummary = await project.docquery.sheetSummary(sheetResult.sheet_id, { orphanLimit: 10 });
  console.log(
    `sheet_summary unreachable_non_sheet=${sheetSummary.reachability.unreachable_non_sheet ?? 0} ` +
      `warnings=${sheetSummary.warnings.length}`
  );
}

const sheetList = await project.docquery.sheetList();
console.log(
  `sheet_list sheet_node_count=${sheetList.totals.sheet_node_count ?? 0} ` +
    `mismatch_warnings=${sheetList.mismatch_warnings.length}`
);

const search = await project.docquery.search(query, { limit: 5 });
console.log(`docquery_search_count=${search.hits.length}`);

const firstUuid = search.hits.find((hit) => hit.node?.properties?.uuid)?.node?.properties?.uuid;
if (typeof firstUuid === 'string' && firstUuid) {
  const node = await project.docquery.nodeGet(firstUuid);
  console.log(`node_get_found=${node.found} uuid=${firstUuid}`);

  const neighbors = await project.docquery.neighbors(firstUuid, {
    mode: 'both',
    direction: 'both',
    radius: 200,
    limit: 10,
  });
  console.log(`neighbors_count=${neighbors.neighbors.length}`);

  const resolved = await project.docquery.referenceResolve(firstUuid, { limit: 10 });
  console.log(`reference_resolve_found=${resolved.found} resolved_count=${resolved.count}`);

  const crop = await project.docquery.crop({
    uuid: firstUuid,
    output: cropOutput,
  });
  console.log(
    `crop path=${crop.output_path} bytes_written=${crop.bytes_written} content_type=${crop.content_type}`
  );
} else {
  console.log('No search hit UUID found; skipping node/neighbors/reference-resolve.');
}

const cypher = await project.docquery.cypher(
  'MATCH (n:Entity {project_id:$project_id}) RETURN count(n) AS total_entities',
  { maxRows: 1 }
);
console.log(`cypher_total_entities=${cypher.records[0]?.total_entities ?? 0}`);

if (cleanup) {
  if (sheetResult.sheet_id) {
    const deletedSheet = await project.sheets.delete(sheetResult.sheet_id);
    console.log(`sheet_deleted=${deletedSheet.deleted} sheet_id=${deletedSheet.sheet_id}`);
  }
  const deletedProject = await openedProject.delete();
  console.log(`project_deleted=${deletedProject.deleted} project_id=${deletedProject.project_id}`);
} else {
  console.log(`kept_project_id=${project.id}`);
}
