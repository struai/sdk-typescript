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
 *   STRUAI_REVIEW_CUSTOM_INSTRUCTIONS="Focus on coordination"
 *   STRUAI_REVIEW_WAIT=1
 *   STRUAI_REVIEW_TIMEOUT_MS=900000
 *   STRUAI_REVIEW_POLL_INTERVAL_MS=5000
 */
import { StruAI } from '../dist/index.mjs';

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

const review = await client.reviews.create({
  file: fileHash ? undefined : pdf,
  fileHash: fileHash || undefined,
  pages: process.env.STRUAI_REVIEW_PAGES ?? process.env.STRUAI_PAGE ?? '13',
  projectIds: parseProjectIds(process.env.STRUAI_REVIEW_PROJECT_IDS),
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
