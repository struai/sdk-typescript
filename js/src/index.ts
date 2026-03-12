/**
 * StruAI JavaScript/TypeScript SDK.
 */

export interface StruAIOptions {
  apiKey: string;
  baseUrl?: string;
  timeout?: number;
}

export type Point = [number, number];
export type BBox = [number, number, number, number];
export type Uploadable = Blob | ArrayBuffer | ArrayBufferView | string;
export type JSONValue =
  | string
  | number
  | boolean
  | null
  | { [key: string]: JSONValue }
  | JSONValue[];

export interface Dimensions {
  width: number;
  height: number;
}

export interface TextSpan {
  id?: string | number | null;
  text: string;
}

export interface Leader {
  id: string;
  bbox?: BBox | null;
  arrow_tip?: Point | null;
  text_bbox?: BBox | null;
  texts_inside: TextSpan[];
}

export interface SectionTag {
  id: string;
  bbox?: BBox | null;
  circle?: { center: Point; radius: number } | null;
  direction?: string | null;
  texts_inside: TextSpan[];
  section_line?: { start: Point; end: Point } | null;
}

export interface DetailTag {
  id: string;
  bbox?: BBox | null;
  circle?: { center: Point; radius: number } | null;
  texts_inside: TextSpan[];
  has_dashed_bbox?: boolean;
}

export interface RevisionTriangle {
  id: string;
  bbox?: BBox | null;
  vertices: Point[];
  text?: string | null;
}

export interface RevisionCloud {
  id: string;
  bbox?: BBox | null;
}

export interface Annotations {
  leaders: Leader[];
  section_tags: SectionTag[];
  detail_tags: DetailTag[];
  revision_triangles: RevisionTriangle[];
  revision_clouds: RevisionCloud[];
}

export interface TitleBlock {
  bounds?: BBox | null;
  viewport?: BBox | null;
}

export interface DrawingResult {
  id: string;
  page: number;
  dimensions: Dimensions;
  processing_ms: number;
  annotations: Annotations;
  titleblock?: TitleBlock | null;
}

export interface DrawingCacheStatus {
  cached: boolean;
  file_hash: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string | null;
  created_at?: string | null;
}

export interface ProjectListResponse {
  projects: Project[];
}

export interface ProjectDeleteResult {
  deleted: boolean;
  project_id: string;
  projects_deleted?: number;
  nodes_deleted?: number;
  relationships_deleted?: number;
  owner_mapping_deleted?: boolean;
  qdrant_deleted_points?: number;
}

export interface ReviewPage {
  page_number: number;
  page_hash: string;
  project_id: string;
}

export interface ReviewProgressCounts {
  pending?: number;
  in_progress?: number;
  completed?: number;
  failed?: number;
  total?: number;
}

export interface ReviewActiveSpecialist {
  question_id: string;
  agent: string;
  turns_used?: number | null;
  max_turns?: number | null;
  updated_at?: string | null;
}

export interface ReviewSpecialistProgress extends ReviewProgressCounts {
  out_of_scope?: number;
  max_turns?: number | null;
  active?: ReviewActiveSpecialist[];
}

export interface ReviewProgress {
  scout?: ReviewProgressCounts;
  specialist?: ReviewSpecialistProgress;
}

export interface Review {
  review_id: string;
  status?: string | null;
  total_pages?: number;
  pages?: ReviewPage[];
  owner_user_id?: string | null;
  file_hash?: string | null;
  page_selector?: string | null;
  requested_project_ids?: string[] | null;
  custom_instructions?: string | null;
  created_at?: string | null;
  completed_at?: string | null;
  progress?: ReviewProgress;
  is_running?: boolean;
  is_complete?: boolean;
  is_partial?: boolean;
  is_failed?: boolean;
  is_terminal?: boolean;
}

export interface ReviewListResponse {
  reviews: Review[];
}

export interface ReviewQuestion {
  question_id: string;
  review_id: string;
  review_page_id?: string | null;
  source: string;
  status: string;
  page_hash: string;
  project_id: string;
  question: string;
  location_description?: string | null;
  assigned_agents: string[];
  spawned_by_question_id?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  turns_used?: number | null;
  error?: string | null;
  raw_model_output?: JSONValue | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ReviewQuestionsResult {
  review_id: string;
  questions: ReviewQuestion[];
}

export interface ReviewIssue {
  issue_id: string;
  review_id: string;
  question_id: string;
  project_id: string;
  page_hash: string;
  agent: string;
  priority: string;
  category?: string | null;
  title: string;
  description: string;
  evidence: string[];
  suggested_fix?: string | null;
  created_at?: string | null;
}

export interface ReviewIssuesResult {
  review_id: string;
  issues: ReviewIssue[];
}

export interface JobSummary {
  job_id: string;
  page: number;
}

export interface SheetIngestResponse {
  jobs: JobSummary[];
}

export interface SheetResult {
  sheet_id?: string;
  entities_created?: number;
  relationships_created?: number;
  skipped?: boolean;
  [key: string]: unknown;
}

export interface JobStatusEvent {
  seq: number;
  event: string;
  status: string;
  at_utc: string;
  message?: string;
  step?: {
    key: string;
    index: number;
    total: number;
    label: string;
  };
  error?: Record<string, unknown>;
}

export interface JobStatus {
  job_id: string;
  page?: number;
  status: 'queued' | 'running' | 'complete' | 'failed' | string;
  created_at_utc?: string | null;
  started_at_utc?: string | null;
  completed_at_utc?: string | null;
  current_step?: string | null;
  step_timings?: Record<string, { start_utc?: string; end_utc?: string; duration_ms?: number }>;
  status_log?: JobStatusEvent[];
  result?: SheetResult;
  error?: string;
}

export interface SheetDeleteResult {
  deleted: boolean;
  project_id: string;
  sheet_id: string;
  nodes_deleted?: number;
  relationships_deleted_by_source_sheet?: number;
  qdrant?: Record<string, unknown>;
}

export interface DocQuerySummaryCounters {
  nodes_created?: number;
  nodes_deleted?: number;
  relationships_created?: number;
  relationships_deleted?: number;
  properties_set?: number;
  labels_added?: number;
  labels_removed?: number;
  indexes_added?: number;
  indexes_removed?: number;
  constraints_added?: number;
  constraints_removed?: number;
  system_updates?: number;
  contains_updates?: boolean;
}

export interface DocQuerySummary {
  database?: string;
  query_type?: string;
  result_available_after_ms?: number;
  result_consumed_after_ms?: number;
  counters?: DocQuerySummaryCounters;
}

export interface DocQuerySearchHit {
  node?: Record<string, unknown>;
  score?: number;
}

export interface DocQueryNeighbor {
  direction?: string;
  relationship?: Record<string, unknown>;
  neighbor?: Record<string, unknown>;
  distance_px?: number | null;
  linked?: boolean;
  edges?: Array<Record<string, unknown>>;
}

export interface DocQueryNodeGetResult {
  ok: boolean;
  found: boolean;
  node?: Record<string, unknown>;
}

export interface DocQuerySheetEntitiesResult {
  ok: boolean;
  entities: Record<string, unknown>[];
}

export interface DocQuerySearchResult {
  ok: boolean;
  hits: DocQuerySearchHit[];
}

export interface DocQueryNeighborsResult {
  ok: boolean;
  mode?: 'graph' | 'spatial' | 'both' | string;
  neighbors: DocQueryNeighbor[];
}

export interface DocQueryCypherResult {
  ok: boolean;
  records: Record<string, unknown>[];
  truncated?: boolean;
}

export interface DocQuerySheetSummaryResult {
  ok: boolean;
  command: string;
  input: Record<string, unknown>;
  sheet_node?: Record<string, unknown>;
  node_label_counts: Record<string, unknown>[];
  relationship_counts: Record<string, unknown>[];
  reachability: Record<string, unknown>;
  orphan_examples: Record<string, unknown>[];
  warnings: Record<string, unknown>[];
}

export interface DocQuerySheetListResult {
  ok: boolean;
  command: string;
  input: Record<string, unknown>;
  sheet_nodes: Record<string, unknown>[];
  entity_sheet_inventory: Record<string, unknown>[];
  totals: Record<string, unknown>;
  mismatch_warnings: Record<string, unknown>[];
}

export interface DocQueryReferenceResolveResult {
  ok: boolean;
  command: string;
  input: Record<string, unknown>;
  found: boolean;
  source?: Record<string, unknown>;
  resolved_references: Record<string, unknown>[];
  count: number;
  warnings: Record<string, unknown>[];
}

export interface DocQueryCropResult {
  ok: boolean;
  output_path: string;
  bytes_written: number;
  content_type: string;
}

const DEFAULT_BASE_URL = 'https://api.stru.ai';

type JsonRecord = Record<string, unknown>;

function normalizeBaseUrl(raw: string): string {
  const trimmed = raw.replace(/\/$/, '');
  try {
    const parsed = new URL(trimmed);
    const path = parsed.pathname.replace(/\/$/, '');
    if (path === '' || path === '/') {
      parsed.pathname = '/v1';
      return parsed.toString().replace(/\/$/, '');
    }
    return trimmed;
  } catch {
    if (trimmed.endsWith('/v1')) {
      return trimmed;
    }
    return `${trimmed}/v1`;
  }
}

export class APIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public code?: string
  ) {
    super(message);
    this.name = 'APIError';
  }
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function parsePageSelector(page: number | string): string {
  if (typeof page === 'number') {
    return String(page);
  }
  const text = page.trim();
  if (!text) {
    throw new Error('page is required');
  }
  return text;
}

function requireText(value: string, fieldName: string): string {
  const text = value.trim();
  if (!text) {
    throw new Error(`${fieldName} is required`);
  }
  return text;
}

function isReviewTerminal(status: string | null | undefined): boolean {
  return status === 'completed' || status === 'completed_partial' || status === 'failed';
}

function withReviewFlags(review: Review): Review {
  const status = review.status ?? undefined;
  return {
    ...review,
    is_running: status === 'running',
    is_complete: status === 'completed',
    is_partial: status === 'completed_partial',
    is_failed: status === 'failed',
    is_terminal: isReviewTerminal(status),
  };
}

function asRecord(value: unknown): JsonRecord | null {
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    return value as JsonRecord;
  }
  return null;
}

function records(payload: DocQueryCypherResult): JsonRecord[] {
  return (payload.records ?? []).map(asRecord).filter((item): item is JsonRecord => item !== null);
}

function asInt(value: unknown): number {
  const num = Number(value);
  return Number.isFinite(num) ? Math.trunc(num) : 0;
}

function parseBBoxInput(bbox: string | BBox | number[]): BBox {
  let parts: string[] | number[];
  if (typeof bbox === 'string') {
    const text = bbox.trim();
    if (!text) {
      throw new Error('bbox is required');
    }
    parts = text.replace(/,/g, ' ').split(/\s+/);
  } else {
    parts = bbox;
  }

  if (parts.length !== 4) {
    throw new Error('bbox must contain four values: x1,y1,x2,y2');
  }

  const values = parts.map((value) => Number(value));
  if (!values.every((value) => Number.isFinite(value))) {
    throw new Error('bbox values must be numeric');
  }

  return [values[0], values[1], values[2], values[3]];
}

function bufferToHex(buffer: ArrayBuffer): string {
  return Array.from(new Uint8Array(buffer))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

function toArrayBuffer(bytes: Uint8Array): ArrayBuffer {
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) as ArrayBuffer;
}

async function readUploadableBytes(file: Uploadable): Promise<Uint8Array> {
  if (typeof file === 'string') {
    const fs = await import('node:fs/promises');
    const data = await fs.readFile(file);
    return new Uint8Array(data.buffer, data.byteOffset, data.byteLength);
  }

  if (file instanceof ArrayBuffer) {
    return new Uint8Array(file);
  }

  if (ArrayBuffer.isView(file)) {
    return new Uint8Array(file.buffer, file.byteOffset, file.byteLength);
  }

  const blob = file as Blob;
  return new Uint8Array(await blob.arrayBuffer());
}

async function computeFileHash(file: Uploadable): Promise<string> {
  const bytes = await readUploadableBytes(file);

  if (globalThis.crypto?.subtle) {
    const digest = await globalThis.crypto.subtle.digest('SHA-256', toArrayBuffer(bytes));
    return bufferToHex(digest).slice(0, 16);
  }

  const crypto = await import('node:crypto');
  const hash = crypto.createHash('sha256').update(Buffer.from(bytes)).digest('hex');
  return hash.slice(0, 16);
}

async function uploadableToFormPart(file: Uploadable): Promise<{ blob: Blob; filename: string }> {
  if (typeof file === 'string') {
    const path = await import('node:path');
    const bytes = await readUploadableBytes(file);
    return {
      blob: new Blob([toArrayBuffer(bytes)], { type: 'application/pdf' }),
      filename: path.basename(file),
    };
  }

  if (file instanceof ArrayBuffer || ArrayBuffer.isView(file)) {
    const bytes = await readUploadableBytes(file);
    return {
      blob: new Blob([toArrayBuffer(bytes)], { type: 'application/pdf' }),
      filename: 'document.pdf',
    };
  }

  const blob = file as Blob;
  const name = (blob as File).name ?? 'document.pdf';
  return { blob, filename: name };
}

class Drawings {
  constructor(private client: StruAI) {}

  async analyze(
    file: Uploadable | null,
    options: { page: number; fileHash?: string }
  ): Promise<DrawingResult> {
    let fileHash = options.fileHash;

    if (fileHash && file) {
      throw new Error('Provide file or fileHash, not both.');
    }
    if (!fileHash && !file) {
      throw new Error('Provide file or fileHash.');
    }

    if (!fileHash && file) {
      const computedHash = await computeFileHash(file);
      const cache = await this.checkCache(computedHash);
      if (cache.cached) {
        fileHash = computedHash;
        file = null;
      }
    }

    const formData = new FormData();
    formData.append('page', String(options.page));
    if (fileHash) {
      formData.append('file_hash', fileHash);
    }
    if (file) {
      const part = await uploadableToFormPart(file);
      formData.append('file', part.blob, part.filename);
    }

    return this.client.request<DrawingResult>('/drawings', {
      method: 'POST',
      body: formData,
    });
  }

  async checkCache(fileHash: string): Promise<DrawingCacheStatus> {
    return this.client.request<DrawingCacheStatus>(`/drawings/cache/${fileHash}`);
  }

  async computeFileHash(file: Uploadable): Promise<string> {
    return computeFileHash(file);
  }
}

class Job {
  constructor(
    private client: StruAI,
    private projectId: string,
    public readonly id: string,
    public readonly page?: number
  ) {}

  async status(): Promise<JobStatus> {
    return this.client.request<JobStatus>(`/projects/${this.projectId}/jobs/${this.id}`);
  }

  async wait(options?: { timeoutMs?: number; pollIntervalMs?: number }): Promise<SheetResult> {
    const timeoutMs = options?.timeoutMs ?? 120_000;
    const pollIntervalMs = options?.pollIntervalMs ?? 2_000;
    const start = Date.now();

    while (Date.now() - start < timeoutMs) {
      const status = await this.status();
      if (status.status === 'complete') {
        return status.result ?? {};
      }
      if (status.status === 'failed') {
        throw new APIError(`Job ${this.id} failed: ${status.error}`);
      }
      await delay(pollIntervalMs);
    }

    throw new APIError(`Job ${this.id} did not complete within ${timeoutMs}ms`);
  }
}

class JobBatch {
  constructor(public readonly jobs: Job[]) {}

  get ids(): string[] {
    return this.jobs.map((job) => job.id);
  }

  async statusAll(): Promise<JobStatus[]> {
    return Promise.all(this.jobs.map((job) => job.status()));
  }

  async waitAll(options?: { timeoutMs?: number; pollIntervalMs?: number }): Promise<SheetResult[]> {
    return Promise.all(this.jobs.map((job) => job.wait(options)));
  }
}

interface AddSheetOptions {
  page: number | string;
  fileHash?: string;
  sourceDescription?: string;
  onSheetExists?: 'error' | 'skip' | 'rebuild';
  communityUpdateMode?: 'incremental' | 'rebuild';
  semanticIndexUpdateMode?: 'incremental' | 'rebuild';
}

class Sheets {
  constructor(
    private client: StruAI,
    private projectId: string
  ) {}

  async add(file: Uploadable | null, options: AddSheetOptions): Promise<Job | JobBatch> {
    let fileHash = options.fileHash;

    if (fileHash && file) {
      throw new Error('Provide file or fileHash, not both.');
    }
    if (!fileHash && !file) {
      throw new Error('Provide file or fileHash.');
    }

    if (!fileHash && file) {
      const computedHash = await computeFileHash(file);
      const cache = await this.client.request<DrawingCacheStatus>(`/drawings/cache/${computedHash}`);
      if (cache.cached) {
        file = null;
        fileHash = computedHash;
      }
    }

    const formData = new FormData();
    formData.append('page', parsePageSelector(options.page));
    if (fileHash) {
      formData.append('file_hash', fileHash);
    }
    if (options.sourceDescription !== undefined) {
      formData.append('source_description', options.sourceDescription);
    }
    if (options.onSheetExists) {
      formData.append('on_sheet_exists', options.onSheetExists);
    }
    if (options.communityUpdateMode) {
      formData.append('community_update_mode', options.communityUpdateMode);
    }
    if (options.semanticIndexUpdateMode) {
      formData.append('semantic_index_update_mode', options.semanticIndexUpdateMode);
    }
    if (file) {
      const part = await uploadableToFormPart(file);
      formData.append('file', part.blob, part.filename);
    }

    const response = await this.client.request<SheetIngestResponse>(`/projects/${this.projectId}/sheets`, {
      method: 'POST',
      body: formData,
    });

    const jobs = (response.jobs ?? []).map(
      (item) => new Job(this.client, this.projectId, item.job_id, item.page)
    );

    if (jobs.length === 1) {
      return jobs[0];
    }
    return new JobBatch(jobs);
  }

  async delete(sheetId: string): Promise<SheetDeleteResult> {
    return this.client.request<SheetDeleteResult>(`/projects/${this.projectId}/sheets/${sheetId}`, {
      method: 'DELETE',
    });
  }

  job(jobId: string, options?: { page?: number }): Job {
    return new Job(this.client, this.projectId, jobId, options?.page);
  }
}

class DocQuery {
  constructor(
    private client: StruAI,
    private projectId: string
  ) {}

  async nodeGet(uuid: string): Promise<DocQueryNodeGetResult> {
    const cleanUuid = requireText(uuid, 'uuid');
    const params = new URLSearchParams({ uuid: cleanUuid });
    return this.client.request<DocQueryNodeGetResult>(
      `/projects/${this.projectId}/node-get?${params.toString()}`
    );
  }

  async sheetEntities(
    sheetId: string,
    options?: { entityType?: string; limit?: number }
  ): Promise<DocQuerySheetEntitiesResult> {
    const cleanSheetId = requireText(sheetId, 'sheet_id');
    const params = new URLSearchParams({
      sheet_id: cleanSheetId,
      limit: String(options?.limit ?? 200),
    });
    if (options?.entityType) {
      params.set('entity_type', options.entityType);
    }
    return this.client.request<DocQuerySheetEntitiesResult>(
      `/projects/${this.projectId}/sheet-entities?${params.toString()}`
    );
  }

  async search(
    query: string,
    options?: { index?: string; limit?: number }
  ): Promise<DocQuerySearchResult> {
    const cleanQuery = requireText(query, 'query');
    const cleanIndex = requireText(options?.index ?? 'entity_search', 'index');
    const params = new URLSearchParams({
      query: cleanQuery,
      index: cleanIndex,
      limit: String(options?.limit ?? 20),
    });
    return this.client.request<DocQuerySearchResult>(
      `/projects/${this.projectId}/search?${params.toString()}`
    );
  }

  async neighbors(
    uuid: string,
    options?: {
      mode?: 'graph' | 'spatial' | 'both';
      direction?: 'in' | 'out' | 'both';
      relationshipType?: string;
      radius?: number;
      limit?: number;
    }
  ): Promise<DocQueryNeighborsResult> {
    const cleanUuid = requireText(uuid, 'uuid');
    const mode = (options?.mode ?? 'both').toLowerCase();
    if (!['graph', 'spatial', 'both'].includes(mode)) {
      throw new Error('mode must be one of: graph, spatial, both');
    }
    const direction = (options?.direction ?? 'both').toLowerCase();
    if (!['in', 'out', 'both'].includes(direction)) {
      throw new Error('direction must be one of: in, out, both');
    }

    const params = new URLSearchParams({
      uuid: cleanUuid,
      mode,
      direction,
      radius: String(options?.radius ?? 200),
      limit: String(options?.limit ?? 50),
    });
    if (options?.relationshipType) {
      params.set('relationship_type', options.relationshipType);
    }

    return this.client.request<DocQueryNeighborsResult>(
      `/projects/${this.projectId}/neighbors?${params.toString()}`
    );
  }

  async cypher(
    query: string,
    options?: { params?: Record<string, unknown>; maxRows?: number }
  ): Promise<DocQueryCypherResult> {
    const cleanQuery = requireText(query, 'query');
    return this.client.request<DocQueryCypherResult>(`/projects/${this.projectId}/cypher`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: cleanQuery,
        params: options?.params ?? {},
        max_rows: options?.maxRows ?? 500,
      }),
    });
  }

  async sheetSummary(sheetId: string, options?: { orphanLimit?: number }): Promise<DocQuerySheetSummaryResult> {
    const cleanSheetId = requireText(sheetId, 'sheet_id');
    const orphanLimit = Math.max(1, Math.min(Math.trunc(options?.orphanLimit ?? 10), 200));

    const sheetNodePayload = await this.cypher(
      'MATCH (s:Entity:Sheet {project_id:$project_id, sheet_id:$sheet_id}) ' +
        'RETURN s.sheet_id AS sheet_id, s.uuid AS uuid, coalesce(s.name, s.text) AS name LIMIT 1',
      { params: { sheet_id: cleanSheetId }, maxRows: 1 }
    );
    const labelCountsPayload = await this.cypher(
      'MATCH (n:Entity {project_id:$project_id, sheet_id:$sheet_id}) ' +
        'UNWIND labels(n) AS label ' +
        "WITH label WHERE label <> 'Entity' " +
        'RETURN label, count(*) AS count ORDER BY count DESC, label',
      { params: { sheet_id: cleanSheetId }, maxRows: 500 }
    );
    const relCountsPayload = await this.cypher(
      'MATCH ()-[r]->() ' +
        'WHERE r.project_id = $project_id ' +
        '  AND $sheet_id IN coalesce(r.source_sheet_ids, []) ' +
        'RETURN type(r) AS rel_type, count(*) AS count ' +
        'ORDER BY count DESC, rel_type',
      { params: { sheet_id: cleanSheetId }, maxRows: 500 }
    );
    const reachabilityPayload = await this.cypher(
      'OPTIONAL MATCH (s:Entity:Sheet {project_id:$project_id, sheet_id:$sheet_id}) ' +
        'MATCH (n:Entity {project_id:$project_id, sheet_id:$sheet_id}) ' +
        'WITH s, collect(n) AS nodes ' +
        'UNWIND nodes AS n ' +
        'WITH s, n, n:Sheet AS is_sheet ' +
        'RETURN ' +
        '(s IS NOT NULL) AS has_sheet_node, ' +
        'count(CASE WHEN is_sheet THEN 1 END) AS sheet_node_count, ' +
        'count(CASE WHEN NOT is_sheet THEN 1 END) AS non_sheet_total, ' +
        'count(CASE WHEN NOT is_sheet AND s IS NOT NULL ' +
        '           AND EXISTS { MATCH (s)<-[:LOCATED_IN*1..2]-(n) } ' +
        '      THEN 1 END) AS reachable_non_sheet',
      { params: { sheet_id: cleanSheetId }, maxRows: 1 }
    );
    const orphanPayload = await this.cypher(
      'MATCH (n:Entity {project_id:$project_id, sheet_id:$sheet_id}) ' +
        'WHERE NOT n:Sheet ' +
        '  AND NOT EXISTS { ' +
        '    MATCH (s:Entity:Sheet {project_id:$project_id, sheet_id:$sheet_id})<-[:LOCATED_IN*1..2]-(n) ' +
        '  } ' +
        'RETURN n.uuid AS uuid, ' +
        "       [l IN labels(n) WHERE l <> 'Entity'] AS labels, " +
        '       n.category AS category, ' +
        '       coalesce(n.name, n.text) AS name ' +
        'ORDER BY coalesce(n.name, n.text), n.uuid ' +
        'LIMIT $orphan_limit',
      { params: { sheet_id: cleanSheetId, orphan_limit: orphanLimit }, maxRows: orphanLimit }
    );

    const sheetRows = records(sheetNodePayload);
    const labelRows = records(labelCountsPayload);
    const relRows = records(relCountsPayload);
    const reachabilityRows = records(reachabilityPayload);
    const orphanRows = records(orphanPayload);

    const reachability: JsonRecord = {
      has_sheet_node: false,
      sheet_node_count: 0,
      non_sheet_total: 0,
      reachable_non_sheet: 0,
      unreachable_non_sheet: 0,
    };

    if (reachabilityRows.length > 0) {
      const first = reachabilityRows[0];
      const hasSheetNode = Boolean(first.has_sheet_node);
      const sheetNodeCount = asInt(first.sheet_node_count);
      const nonSheetTotal = asInt(first.non_sheet_total);
      const reachableNonSheet = asInt(first.reachable_non_sheet);
      reachability.has_sheet_node = hasSheetNode;
      reachability.sheet_node_count = sheetNodeCount;
      reachability.non_sheet_total = nonSheetTotal;
      reachability.reachable_non_sheet = reachableNonSheet;
      reachability.unreachable_non_sheet = Math.max(0, nonSheetTotal - reachableNonSheet);
    }

    const warnings: JsonRecord[] = [];
    if (!Boolean(reachability.has_sheet_node)) {
      warnings.push({
        type: 'missing_sheet_node',
        message: `No :Entity:Sheet node found for sheet_id=${cleanSheetId}.`,
      });
    }
    if (asInt(reachability.sheet_node_count) > 1) {
      warnings.push({
        type: 'duplicate_sheet_nodes',
        message: `Found ${asInt(reachability.sheet_node_count)} Sheet nodes for sheet_id=${cleanSheetId}; expected 1.`,
      });
    }
    if (asInt(reachability.unreachable_non_sheet) > 0) {
      warnings.push({
        type: 'unreachable_entities',
        message:
          `${asInt(reachability.unreachable_non_sheet)} non-sheet entities are not reachable ` +
          `from sheet ${cleanSheetId} via LOCATED_IN*1..2.`,
      });
    }

    return {
      ok: true,
      command: 'sheet-summary',
      input: {
        project_id: this.projectId,
        sheet_id: cleanSheetId,
        orphan_limit: orphanLimit,
      },
      sheet_node: sheetRows[0],
      node_label_counts: labelRows,
      relationship_counts: relRows,
      reachability,
      orphan_examples: orphanRows,
      warnings,
    };
  }

  async sheetList(): Promise<DocQuerySheetListResult> {
    const sheetNodesPayload = await this.cypher(
      'MATCH (s:Entity:Sheet {project_id:$project_id}) ' +
        'RETURN s.sheet_id AS sheet_id, s.uuid AS uuid, coalesce(s.name, s.text) AS name ' +
        'ORDER BY s.sheet_id, s.uuid',
      { maxRows: 5000 }
    );
    const inventoryPayload = await this.cypher(
      'MATCH (n:Entity {project_id:$project_id}) ' +
        'RETURN n.sheet_id AS sheet_id, count(n) AS entity_count ' +
        'ORDER BY n.sheet_id',
      { maxRows: 5000 }
    );
    const duplicateSheetNodesPayload = await this.cypher(
      'MATCH (s:Entity:Sheet {project_id:$project_id}) ' +
        'WITH s.sheet_id AS sheet_id, count(*) AS sheet_node_count ' +
        'WHERE sheet_node_count > 1 ' +
        'RETURN sheet_id, sheet_node_count ' +
        'ORDER BY sheet_node_count DESC, sheet_id',
      { maxRows: 200 }
    );
    const missingSheetIdPayload = await this.cypher(
      'MATCH (n:Entity {project_id:$project_id}) ' +
        "WHERE n.sheet_id IS NULL OR trim(toString(n.sheet_id)) = '' " +
        'RETURN count(n) AS missing_sheet_id_count',
      { maxRows: 1 }
    );

    const sheetNodes = records(sheetNodesPayload);
    const inventory = records(inventoryPayload);
    const duplicateSheetNodes = records(duplicateSheetNodesPayload);
    const missingSheetRows = records(missingSheetIdPayload);
    const missingSheetIdCount = missingSheetRows.length > 0 ? asInt(missingSheetRows[0].missing_sheet_id_count) : 0;

    const sheetNodeIds = new Set(
      sheetNodes
        .map((row) => row.sheet_id)
        .filter((id): id is string => typeof id === 'string' && id.trim().length > 0)
    );
    const inventoryIds = new Set(
      inventory
        .map((row) => row.sheet_id)
        .filter((id): id is string => typeof id === 'string' && id.trim().length > 0)
    );

    const inventoryCounts = new Map<string, number>();
    for (const row of inventory) {
      if (typeof row.sheet_id === 'string' && row.sheet_id.trim()) {
        inventoryCounts.set(row.sheet_id, asInt(row.entity_count));
      }
    }

    const totalEntities = inventory.reduce((sum, row) => sum + asInt(row.entity_count), 0);
    const inventoryWithoutSheetNode = [...inventoryIds].filter((id) => !sheetNodeIds.has(id)).sort();
    const sheetNodesWithoutInventory = [...sheetNodeIds].filter((id) => !inventoryIds.has(id)).sort();
    const sheetNodesWithOnlySelf = [...sheetNodeIds].filter((id) => (inventoryCounts.get(id) ?? 0) === 1).sort();

    const mismatchWarnings: JsonRecord[] = [];
    if (inventoryWithoutSheetNode.length > 0) {
      mismatchWarnings.push({
        type: 'inventory_sheet_id_without_sheet_node',
        sheet_ids: inventoryWithoutSheetNode,
        message: 'Entities exist for sheet_id values that do not have a Sheet node.',
      });
    }
    if (sheetNodesWithoutInventory.length > 0) {
      mismatchWarnings.push({
        type: 'sheet_node_without_inventory',
        sheet_ids: sheetNodesWithoutInventory,
        message: 'Sheet nodes exist with no matching entity inventory rows.',
      });
    }
    if (duplicateSheetNodes.length > 0) {
      mismatchWarnings.push({
        type: 'duplicate_sheet_nodes',
        duplicates: duplicateSheetNodes,
        message: 'Multiple Sheet nodes found for one or more sheet_id values.',
      });
    }
    if (missingSheetIdCount > 0) {
      mismatchWarnings.push({
        type: 'entities_missing_sheet_id',
        count: missingSheetIdCount,
        message: 'Some entities are missing sheet_id.',
      });
    }
    if (sheetNodesWithOnlySelf.length > 0) {
      mismatchWarnings.push({
        type: 'sheet_nodes_without_non_sheet_entities',
        sheet_ids: sheetNodesWithOnlySelf,
        message: 'Sheet IDs where inventory count is only the Sheet node itself.',
      });
    }

    return {
      ok: true,
      command: 'sheet-list',
      input: {
        project_id: this.projectId,
      },
      sheet_nodes: sheetNodes,
      entity_sheet_inventory: inventory,
      totals: {
        sheet_node_count: sheetNodes.length,
        inventory_sheet_id_count: inventoryIds.size,
        total_entities: totalEntities,
        missing_sheet_id_count: missingSheetIdCount,
      },
      mismatch_warnings: mismatchWarnings,
    };
  }

  async referenceResolve(
    uuid: string,
    options?: { limit?: number }
  ): Promise<DocQueryReferenceResolveResult> {
    const nodeUuid = requireText(uuid, 'uuid');
    const limit = Math.max(1, Math.min(Math.trunc(options?.limit ?? 100), 200));

    const sourcePayload = await this.cypher(
      'MATCH (src:Entity {project_id:$project_id, uuid:$uuid}) ' +
        'RETURN src.uuid AS uuid, ' +
        "       [l IN labels(src) WHERE l <> 'Entity'] AS labels, " +
        '       src.sheet_id AS sheet_id, ' +
        '       src.detail_id AS detail_id, ' +
        '       src.section_id AS section_id, ' +
        '       src.target_sheets AS target_sheets, ' +
        '       src.category AS category, ' +
        '       coalesce(src.name, src.text) AS name, ' +
        '       src.text AS text ' +
        'LIMIT 1',
      { params: { uuid: nodeUuid }, maxRows: 1 }
    );

    const sourceRows = records(sourcePayload);
    if (sourceRows.length === 0) {
      return {
        ok: true,
        command: 'reference-resolve',
        input: { project_id: this.projectId, uuid: nodeUuid, limit },
        found: false,
        source: undefined,
        resolved_references: [],
        count: 0,
        warnings: [{ type: 'source_not_found', message: 'No source node found for uuid.' }],
      };
    }

    const source = sourceRows[0];
    const sourceLabels = Array.isArray(source.labels)
      ? source.labels.filter((label): label is string => typeof label === 'string')
      : [];
    const sourceTargetSheets = Array.isArray(source.target_sheets)
      ? source.target_sheets.map((item) => String(item))
      : [];

    const referencesPayload = await this.cypher(
      'MATCH (src:Entity {project_id:$project_id, uuid:$uuid}) ' +
        'OPTIONAL MATCH (src)-[r:REFERENCES]->(t:Entity {project_id:$project_id}) ' +
        'OPTIONAL MATCH (t)-[:LOCATED_IN]->(loc1:Entity {project_id:$project_id}) ' +
        'OPTIONAL MATCH (loc1)-[:LOCATED_IN]->(loc2:Entity {project_id:$project_id}) ' +
        'RETURN r.rel_uuid AS rel_uuid, ' +
        '       r.fact AS fact, ' +
        '       r.source_sheet_ids AS source_sheet_ids, ' +
        '       r.meta_target_sheet AS meta_target_sheet, ' +
        '       r.meta_target_detail_id AS meta_target_detail_id, ' +
        '       r.meta_target_section_id AS meta_target_section_id, ' +
        '       r.meta_target_kind AS meta_target_kind, ' +
        '       t.uuid AS target_uuid, ' +
        "       [l IN labels(t) WHERE l <> 'Entity'] AS target_labels, " +
        '       t.sheet_id AS target_sheet_id, ' +
        '       t.detail_id AS target_detail_id, ' +
        '       t.section_id AS target_section_id, ' +
        '       t.category AS target_category, ' +
        '       coalesce(t.name, t.text) AS target_name, ' +
        '       loc1.uuid AS target_located_in_uuid_1, ' +
        "       [l IN labels(loc1) WHERE l <> 'Entity'] AS target_located_in_labels_1, " +
        '       coalesce(loc1.name, loc1.text) AS target_located_in_name_1, ' +
        '       loc2.uuid AS target_located_in_uuid_2, ' +
        "       [l IN labels(loc2) WHERE l <> 'Entity'] AS target_located_in_labels_2, " +
        '       coalesce(loc2.name, loc2.text) AS target_located_in_name_2 ' +
        "ORDER BY coalesce(t.sheet_id, ''), coalesce(t.name, t.text, ''), t.uuid " +
        'LIMIT $limit',
      { params: { uuid: nodeUuid, limit }, maxRows: limit }
    );

    const referenceRows = records(referencesPayload);
    const resolvedReferences: JsonRecord[] = [];
    const warnings: JsonRecord[] = [];
    const seen = new Set<string>();

    for (const row of referenceRows) {
      const relUuid = row.rel_uuid;
      const targetUuid = row.target_uuid;
      if (relUuid == null && targetUuid == null) {
        continue;
      }

      const key = JSON.stringify([
        relUuid,
        targetUuid,
        row.target_located_in_uuid_1,
        row.target_located_in_uuid_2,
      ]);
      if (seen.has(key)) {
        continue;
      }
      seen.add(key);

      const targetSheetId = row.target_sheet_id;
      const metaTargetSheet = row.meta_target_sheet;

      let sheetMatchMeta: boolean | null = null;
      if (targetSheetId != null && metaTargetSheet != null) {
        sheetMatchMeta = String(targetSheetId) === String(metaTargetSheet);
      }

      let sheetInSourceTargets: boolean | null = null;
      if (targetSheetId != null && sourceTargetSheets.length > 0) {
        sheetInSourceTargets = sourceTargetSheets.includes(String(targetSheetId));
      }

      const traversalPath: JsonRecord[] = [
        { from_uuid: nodeUuid, rel_type: 'REFERENCES', to_uuid: targetUuid as string | undefined },
      ];
      if (row.target_located_in_uuid_1) {
        traversalPath.push({
          from_uuid: targetUuid as string | undefined,
          rel_type: 'LOCATED_IN',
          to_uuid: row.target_located_in_uuid_1 as string,
        });
      }
      if (row.target_located_in_uuid_2) {
        traversalPath.push({
          from_uuid: row.target_located_in_uuid_1 as string | undefined,
          rel_type: 'LOCATED_IN',
          to_uuid: row.target_located_in_uuid_2 as string,
        });
      }

      resolvedReferences.push({
        relationship: {
          rel_uuid: relUuid,
          fact: row.fact,
          source_sheet_ids: row.source_sheet_ids,
          meta_target_sheet: metaTargetSheet,
          meta_target_detail_id: row.meta_target_detail_id,
          meta_target_section_id: row.meta_target_section_id,
          meta_target_kind: row.meta_target_kind,
        },
        target: {
          uuid: targetUuid,
          labels: row.target_labels,
          sheet_id: targetSheetId,
          detail_id: row.target_detail_id,
          section_id: row.target_section_id,
          category: row.target_category,
          name: row.target_name,
        },
        target_context: {
          located_in_1: {
            uuid: row.target_located_in_uuid_1,
            labels: row.target_located_in_labels_1,
            name: row.target_located_in_name_1,
          },
          located_in_2: {
            uuid: row.target_located_in_uuid_2,
            labels: row.target_located_in_labels_2,
            name: row.target_located_in_name_2,
          },
        },
        checks: {
          target_sheet_matches_meta_target_sheet: sheetMatchMeta,
          target_sheet_in_source_target_sheets: sheetInSourceTargets,
        },
        traversal_path: traversalPath,
      });

      if (sheetMatchMeta === false) {
        warnings.push({
          type: 'meta_target_sheet_mismatch',
          rel_uuid: relUuid,
          message: 'Target sheet_id does not match relationship meta_target_sheet.',
        });
      }
      if (sheetInSourceTargets === false) {
        warnings.push({
          type: 'source_target_sheets_mismatch',
          rel_uuid: relUuid,
          message: 'Target sheet_id is not listed in source target_sheets.',
        });
      }
    }

    if (!sourceLabels.includes('Callout')) {
      warnings.push({
        type: 'source_not_callout',
        message: 'Source node is not labeled Callout; references may still exist.',
      });
    }
    if (resolvedReferences.length === 0) {
      warnings.push({
        type: 'no_outgoing_references',
        message: 'No outgoing REFERENCES edges found for this source node.',
      });
    }

    return {
      ok: true,
      command: 'reference-resolve',
      input: { project_id: this.projectId, uuid: nodeUuid, limit },
      found: true,
      source,
      resolved_references: resolvedReferences,
      count: resolvedReferences.length,
      warnings,
    };
  }

  async crop(options: {
    output: string;
    uuid?: string;
    bbox?: string | BBox | number[];
    pageHash?: string;
  }): Promise<DocQueryCropResult> {
    const hasUuid = typeof options.uuid === 'string' && options.uuid.trim().length > 0;
    const hasBbox = options.bbox !== undefined;
    if (hasUuid === hasBbox) {
      throw new Error('provide exactly one of uuid or bbox');
    }

    const output = requireText(options.output, 'output');
    const path = await import('node:path');
    const fs = await import('node:fs/promises');

    const outputPath = path.resolve(process.cwd(), output);
    await fs.mkdir(path.dirname(outputPath), { recursive: true });

    const body: Record<string, unknown> = {};
    if (hasUuid) {
      body.uuid = requireText(options.uuid as string, 'uuid');
    } else {
      body.bbox = parseBBoxInput(options.bbox as string | BBox | number[]);
      body.page_hash = requireText(options.pageHash ?? '', 'pageHash');
    }

    const bytesResponse = await this.client.requestBytes(`/projects/${this.projectId}/crop`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    await fs.writeFile(outputPath, Buffer.from(bytesResponse.bytes));

    return {
      ok: true,
      output_path: outputPath,
      bytes_written: bytesResponse.bytes.length,
      content_type: bytesResponse.contentType ?? 'image/png',
    };
  }
}

class ProjectInstance {
  public readonly sheets: Sheets;
  public readonly docquery: DocQuery;

  constructor(
    private client: StruAI,
    private project: Project
  ) {
    this.sheets = new Sheets(client, project.id);
    this.docquery = new DocQuery(client, project.id);
  }

  get id(): string {
    return this.project.id;
  }

  get name(): string {
    return this.project.name;
  }

  get description(): string | null | undefined {
    return this.project.description;
  }

  get data(): Project {
    return this.project;
  }

  async delete(): Promise<ProjectDeleteResult> {
    return this.client.request<ProjectDeleteResult>(`/projects/${this.id}`, { method: 'DELETE' });
  }
}

class Projects {
  constructor(private client: StruAI) {}

  async create(options: { name: string; description?: string }): Promise<ProjectInstance> {
    const project = await this.client.request<Project>('/projects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(options),
    });
    return new ProjectInstance(this.client, project);
  }

  async list(): Promise<Project[]> {
    const response = await this.client.request<ProjectListResponse>('/projects');
    return response.projects ?? [];
  }

  open(projectId: string, options?: { name?: string; description?: string | null }): ProjectInstance {
    const cleanProjectId = requireText(projectId, 'project_id');
    return new ProjectInstance(this.client, {
      id: cleanProjectId,
      name: options?.name ?? cleanProjectId,
      description: options?.description ?? undefined,
    });
  }

  async delete(projectId: string): Promise<ProjectDeleteResult> {
    const cleanProjectId = requireText(projectId, 'project_id');
    return this.client.request<ProjectDeleteResult>(`/projects/${cleanProjectId}`, { method: 'DELETE' });
  }
}

class ReviewInstance {
  constructor(
    private client: StruAI,
    private review: Review
  ) {
    this.review = withReviewFlags(review);
  }

  get id(): string {
    return this.review.review_id;
  }

  get data(): Review {
    return this.review;
  }

  async refresh(): Promise<Review> {
    this.review = withReviewFlags(await this.client.request<Review>(`/reviews/${this.id}`));
    return this.review;
  }

  async status(): Promise<Review> {
    return this.refresh();
  }

  async questions(): Promise<ReviewQuestion[]> {
    const response = await this.client.request<ReviewQuestionsResult>(`/reviews/${this.id}/questions`);
    return response.questions ?? [];
  }

  async issues(): Promise<ReviewIssue[]> {
    const response = await this.client.request<ReviewIssuesResult>(`/reviews/${this.id}/issues`);
    return response.issues ?? [];
  }

  async wait(options?: { timeoutMs?: number; pollIntervalMs?: number }): Promise<Review> {
    const timeoutMs = options?.timeoutMs ?? 900_000;
    const pollIntervalMs = options?.pollIntervalMs ?? 5_000;
    const start = Date.now();

    let latest = this.review;
    while (Date.now() - start < timeoutMs) {
      if (latest.is_failed) {
        throw new APIError(`Review ${this.id} failed`);
      }
      if (isReviewTerminal(latest.status)) {
        this.review = latest;
        return latest;
      }
      await delay(pollIntervalMs);
      latest = await this.refresh();
    }

    throw new APIError(`Review ${this.id} did not complete within ${timeoutMs}ms`);
  }
}

class Reviews {
  constructor(private client: StruAI) {}

  async create(options: {
    file?: Uploadable | null;
    pages: number | string;
    fileHash?: string;
    projectIds?: string[];
    customInstructions?: string | null;
  }): Promise<ReviewInstance> {
    const uploadFile = options.file;
    const fileHash = options.fileHash;
    const pages = parsePageSelector(options.pages);

    if (uploadFile && fileHash) {
      throw new Error('Provide file or fileHash, not both.');
    }
    if (!uploadFile && !fileHash) {
      throw new Error('Provide file or fileHash.');
    }

    if (fileHash) {
      const review = await this.client.request<Review>('/reviews', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_hash: fileHash,
          pages,
          project_ids: options.projectIds,
          custom_instructions: options.customInstructions ?? undefined,
        }),
      });
      return new ReviewInstance(this.client, withReviewFlags(review));
    }

    if (!uploadFile) {
      throw new Error('Provide file or fileHash.');
    }

    const formData = new FormData();
    formData.append('pages', pages);
    for (const projectId of options.projectIds ?? []) {
      const cleanProjectId = projectId.trim();
      if (cleanProjectId) {
        formData.append('project_ids', cleanProjectId);
      }
    }
    if (options.customInstructions !== undefined && options.customInstructions !== null) {
      formData.append('custom_instructions', options.customInstructions);
    }

    const part = await uploadableToFormPart(uploadFile);
    formData.append('file', part.blob, part.filename);

    const review = await this.client.request<Review>('/reviews', {
      method: 'POST',
      body: formData,
    });
    return new ReviewInstance(this.client, withReviewFlags(review));
  }

  async list(options?: { status?: string }): Promise<Review[]> {
    const path = options?.status
      ? `/reviews?status=${encodeURIComponent(options.status)}`
      : '/reviews';
    const response = await this.client.request<ReviewListResponse>(path);
    return (response.reviews ?? []).map(withReviewFlags);
  }

  async get(reviewId: string): Promise<ReviewInstance> {
    const cleanReviewId = requireText(reviewId, 'review_id');
    const review = withReviewFlags(await this.client.request<Review>(`/reviews/${cleanReviewId}`));
    return new ReviewInstance(this.client, review);
  }

  open(reviewId: string): ReviewInstance {
    const cleanReviewId = requireText(reviewId, 'review_id');
    return new ReviewInstance(this.client, withReviewFlags({ review_id: cleanReviewId }));
  }
}

export class StruAI {
  private apiKey: string;
  private baseUrl: string;
  private timeout: number;

  public readonly drawings: Drawings;
  public readonly projects: Projects;
  public readonly reviews: Reviews;

  constructor(options: StruAIOptions) {
    this.apiKey = options.apiKey;
    this.baseUrl = normalizeBaseUrl(options.baseUrl ?? DEFAULT_BASE_URL);
    this.timeout = options.timeout ?? 60_000;

    this.drawings = new Drawings(this);
    this.projects = new Projects(this);
    this.reviews = new Reviews(this);
  }

  async request<T>(path: string, init?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const headers = new Headers(init?.headers);
    headers.set('Authorization', `Bearer ${this.apiKey}`);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...init,
        headers,
        signal: controller.signal,
      });

      if (!response.ok) {
        let message = response.statusText;
        let code: string | undefined;
        try {
          const body = (await response.json()) as { error?: { message?: string; code?: string } };
          message = body?.error?.message ?? message;
          code = body?.error?.code;
        } catch {
          // Ignore JSON parse failure and keep status text.
        }
        throw new APIError(message, response.status, code);
      }

      if (response.status === 204) {
        return undefined as T;
      }

      const text = await response.text();
      if (!text) {
        return undefined as T;
      }
      return JSON.parse(text) as T;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  async requestBytes(
    path: string,
    init?: RequestInit
  ): Promise<{ bytes: Uint8Array; contentType: string | null }> {
    const url = `${this.baseUrl}${path}`;
    const headers = new Headers(init?.headers);
    headers.set('Authorization', `Bearer ${this.apiKey}`);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...init,
        headers,
        signal: controller.signal,
      });

      if (!response.ok) {
        let message = response.statusText;
        let code: string | undefined;
        try {
          const body = (await response.json()) as { error?: { message?: string; code?: string } };
          message = body?.error?.message ?? message;
          code = body?.error?.code;
        } catch {
          // Ignore JSON parse failure and keep status text.
        }
        throw new APIError(message, response.status, code);
      }

      const buffer = await response.arrayBuffer();
      return {
        bytes: new Uint8Array(buffer),
        contentType: response.headers.get('content-type'),
      };
    } finally {
      clearTimeout(timeoutId);
    }
  }
}

export { Job, JobBatch, ProjectInstance, Projects, Drawings, Sheets, DocQuery };
export default StruAI;
