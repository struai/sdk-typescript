/**
 * Drawings-only workflow example.
 *
 * Usage:
 *   npm run build
 *   STRUAI_API_KEY=... \
 *   STRUAI_PDF=/absolute/path/to/structural.pdf STRUAI_PAGE=12 \
 *   node scripts/drawings_quickstart.mjs
 */

import fs from 'node:fs/promises';
import path from 'node:path';
import { StruAI } from '../dist/index.mjs';

const apiKey = process.env.STRUAI_API_KEY;
const baseUrl = process.env.STRUAI_BASE_URL ?? 'https://api.stru.ai';
const pdfPath = process.env.STRUAI_PDF;
const page = Number(process.env.STRUAI_PAGE ?? '12');

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

const fileHash = await client.drawings.computeFileHash(pdfPath);
const cache = await client.drawings.checkCache(fileHash);
console.log(`file_hash=${fileHash} cached=${cache.cached}`);

const drawing = cache.cached
  ? await client.drawings.analyze(null, { page, fileHash })
  : await client.drawings.analyze(pdfPath, { page });

console.log(`drawing_id=${drawing.id} page=${drawing.page} processing_ms=${drawing.processing_ms}`);
console.log(
  `leaders=${drawing.annotations.leaders.length} ` +
    `section_tags=${drawing.annotations.section_tags.length} ` +
    `detail_tags=${drawing.annotations.detail_tags.length} ` +
    `revision_triangles=${drawing.annotations.revision_triangles.length} ` +
    `revision_clouds=${drawing.annotations.revision_clouds.length}`
);
console.log('drawings_get_delete_endpoints_removed=true');

console.log(`pdf_name=${path.basename(pdfPath)}`);
