/**
 * Portable review workflow example for StruAI JS SDK.
 *
 * Required:
 *   STRUAI_API_KEY
 *   STRUAI_REVIEW_FILE_HASH or STRUAI_PDF
 *
 * Optional:
 *   STRUAI_BASE_URL=https://api.stru.ai  (default; override for local dev)
 *   STRUAI_REVIEW_PAGES=13
 *   STRUAI_REVIEW_PROJECT_IDS=proj_1,proj_2
 *   STRUAI_REVIEW_SCOUT_FILE=/absolute/path/to/scout.md
 *   STRUAI_REVIEW_SPECIALISTS_COMMON_FILE=/absolute/path/to/specialists_common.md
 *   STRUAI_REVIEW_SPECIALISTS_FILE=/absolute/path/to/specialists.json
 *   STRUAI_REVIEW_CUSTOM_INSTRUCTIONS="Focus on coordination"
 *   STRUAI_REVIEW_WAIT=1
 *   STRUAI_REVIEW_TIMEOUT_MS=900000
 *   STRUAI_REVIEW_POLL_INTERVAL_MS=5000
 */
import { StruAI } from '../dist/index.mjs';
import fs from 'node:fs/promises';

function parseProjectIds(rawValue) {
  return (rawValue ?? '')
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean);
}

function serializeReview(review) {
  return {
    review_id: review.review_id,
    status: review.status,
    total_pages: review.total_pages,
    pages: review.pages ?? [],
    progress: review.progress ?? null,
  };
}

async function readOptionalTextFile(pathValue) {
  if (!pathValue) return undefined;
  const text = (await fs.readFile(pathValue, 'utf8')).trim();
  return text || undefined;
}

async function readSpecialistsFile(pathValue) {
  if (!pathValue) return undefined;
  const raw = await fs.readFile(pathValue, 'utf8');
  const payload = JSON.parse(raw);
  if (!Array.isArray(payload)) {
    throw new Error('STRUAI_REVIEW_SPECIALISTS_FILE must contain a JSON array');
  }
  return payload;
}

const apiKey = process.env.STRUAI_API_KEY;
if (!apiKey) {
  throw new Error('Missing STRUAI_API_KEY');
}

const fileHash = process.env.STRUAI_REVIEW_FILE_HASH?.trim();
const pdf = process.env.STRUAI_PDF?.trim();
if (!fileHash && !pdf) {
  throw new Error('Provide STRUAI_REVIEW_FILE_HASH or STRUAI_PDF');
}

const client = new StruAI({
  apiKey,
  baseUrl: process.env.STRUAI_BASE_URL ?? 'https://api.stru.ai',
});

const scout = await readOptionalTextFile(process.env.STRUAI_REVIEW_SCOUT_FILE?.trim());
const specialistsCommon = await readOptionalTextFile(
  process.env.STRUAI_REVIEW_SPECIALISTS_COMMON_FILE?.trim()
);
const specialists = await readSpecialistsFile(process.env.STRUAI_REVIEW_SPECIALISTS_FILE?.trim());

const review = await client.reviews.create({
  file: fileHash ? undefined : pdf,
  fileHash: fileHash || undefined,
  pages: process.env.STRUAI_REVIEW_PAGES ?? process.env.STRUAI_PAGE ?? '13',
  projectIds: parseProjectIds(process.env.STRUAI_REVIEW_PROJECT_IDS),
  scout,
  specialistsCommon,
  specialists,
  customInstructions: process.env.STRUAI_REVIEW_CUSTOM_INSTRUCTIONS ?? undefined,
});

console.log(`created_review=${JSON.stringify(serializeReview(review.data), null, 2)}`);

const refreshed = await review.refresh();
console.log(`refreshed_review=${JSON.stringify(serializeReview(refreshed), null, 2)}`);

if (process.env.STRUAI_REVIEW_WAIT === '1') {
  const finalReview = await review.wait({
    timeoutMs: Number(process.env.STRUAI_REVIEW_TIMEOUT_MS ?? 900_000),
    pollIntervalMs: Number(process.env.STRUAI_REVIEW_POLL_INTERVAL_MS ?? 5_000),
  });
  const questions = await review.questions();
  const issues = await review.issues();
  console.log(`final_review=${JSON.stringify(serializeReview(finalReview), null, 2)}`);
  console.log(
    `review_counts review_id=${review.id} questions=${questions.length} issues=${issues.length}`
  );
}
