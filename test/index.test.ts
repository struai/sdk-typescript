import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { APIError, Job, JobBatch, StruAI } from '../src/index';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function pngResponse(bytes: Uint8Array, status = 200): Response {
  return new Response(bytes, {
    status,
    headers: { 'Content-Type': 'image/png' },
  });
}

describe('StruAI JS SDK', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('normalizes baseUrl by appending /v1', () => {
    const client = new StruAI({ apiKey: 'k', baseUrl: 'http://localhost:8000' });
    expect((client as any).baseUrl).toBe('http://localhost:8000/v1');
  });

  it('opens a project handle without a network lookup', () => {
    const client = new StruAI({ apiKey: 'k', baseUrl: 'http://localhost:8000' });
    const project = client.projects.open('proj_123', { name: 'Test Project' });
    expect(project.id).toBe('proj_123');
    expect(project.name).toBe('Test Project');
  });

  it('returns Job for single-page ingest and JobBatch for multi-page ingest', async () => {
    const fetchMock = vi
      .fn<Parameters<typeof fetch>, ReturnType<typeof fetch>>()
      .mockResolvedValueOnce(jsonResponse({ id: 'proj_1', name: 'Project 1' }))
      .mockResolvedValueOnce(jsonResponse({ jobs: [{ job_id: 'job_1', page: 1 }] }))
      .mockResolvedValueOnce(
        jsonResponse({
          jobs: [
            { job_id: 'job_2', page: 1 },
            { job_id: 'job_3', page: 2 },
          ],
        })
      );

    vi.stubGlobal('fetch', fetchMock);

    const client = new StruAI({ apiKey: 'k', baseUrl: 'http://localhost:8000' });
    const project = await client.projects.create({ name: 'Project 1' });

    const single = await project.sheets.add(null, { page: 1, fileHash: 'abc123def4567890' });
    expect(single).toBeInstanceOf(Job);

    const multi = await project.sheets.add(null, { page: '1,2', fileHash: 'abc123def4567890' });
    expect(multi).toBeInstanceOf(JobBatch);
    expect((multi as JobBatch).ids).toEqual(['job_2', 'job_3']);
  });

  it('parses docquery search payload', async () => {
    const fetchMock = vi
      .fn<Parameters<typeof fetch>, ReturnType<typeof fetch>>()
      .mockResolvedValueOnce(jsonResponse({ id: 'proj_1', name: 'Project 1' }))
      .mockResolvedValueOnce(
        jsonResponse({
          ok: true,
          hits: [{ node: { properties: { uuid: 'node_1' } }, score: 0.88 }],
        })
      );

    vi.stubGlobal('fetch', fetchMock);

    const client = new StruAI({ apiKey: 'k', baseUrl: 'http://localhost:8000' });
    const project = await client.projects.create({ name: 'Project 1' });

    const result = await project.docquery.search('beam', { limit: 5 });
    expect(result.hits.length).toBe(1);
    expect(result.hits[0].score).toBe(0.88);
    expect((result.hits[0].node as any).properties.uuid).toBe('node_1');
    expect(fetchMock).toHaveBeenLastCalledWith(
      'http://localhost:8000/v1/projects/proj_1/search?query=beam&index=entity_search&limit=5',
      expect.any(Object)
    );
  });

  it('builds sheetSummary from docquery cypher calls', async () => {
    const cypher = (records: Array<Record<string, unknown>>) =>
      jsonResponse({
        ok: true,
        records,
      });

    const fetchMock = vi
      .fn<Parameters<typeof fetch>, ReturnType<typeof fetch>>()
      .mockResolvedValueOnce(jsonResponse({ id: 'proj_1', name: 'Project 1' }))
      .mockResolvedValueOnce(cypher([]))
      .mockResolvedValueOnce(cypher([{ label: 'Callout', count: 2 }]))
      .mockResolvedValueOnce(cypher([{ rel_type: 'REFERENCES', count: 5 }]))
      .mockResolvedValueOnce(
        cypher([
          {
            has_sheet_node: false,
            sheet_node_count: 0,
            non_sheet_total: 3,
            reachable_non_sheet: 1,
          },
        ])
      )
      .mockResolvedValueOnce(cypher([{ uuid: 'u1', labels: ['Callout'], category: 'callout', name: 'A' }]));

    vi.stubGlobal('fetch', fetchMock);

    const client = new StruAI({ apiKey: 'k', baseUrl: 'http://localhost:8000' });
    const project = await client.projects.create({ name: 'Project 1' });

    const summary = await project.docquery.sheetSummary('S111', { orphanLimit: 5 });
    expect(summary.command).toBe('sheet-summary');
    expect(summary.reachability.unreachable_non_sheet).toBe(2);
    expect(summary.warnings.map((w) => w.type)).toContain('missing_sheet_node');
    expect(summary.orphan_examples.length).toBe(1);
  });

  it('crops via server endpoint and writes png output', async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'struai-crop-'));
    const outputPath = path.join(tmpDir, 'crop.png');
    const bodyBytes = new Uint8Array([137, 80, 78, 71, 1, 2, 3, 4]);
    const fetchMock = vi
      .fn<Parameters<typeof fetch>, ReturnType<typeof fetch>>()
      .mockResolvedValueOnce(pngResponse(bodyBytes));

    vi.stubGlobal('fetch', fetchMock);

    const client = new StruAI({ apiKey: 'k', baseUrl: 'http://localhost:8000' });
    const project = client.projects.open('proj_1');
    const result = await project.docquery.crop({
      output: outputPath,
      bbox: [10, 15, 50, 45],
      pageHash: 'page_hash_1',
    });

    expect(result.ok).toBe(true);
    expect(result.output_path).toBe(outputPath);
    expect(result.bytes_written).toBe(bodyBytes.length);
    expect(result.content_type).toContain('image/png');

    const written = await fs.readFile(outputPath);
    expect(written.length).toBe(bodyBytes.length);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('http://localhost:8000/v1/projects/proj_1/crop');
    expect((init as RequestInit).method).toBe('POST');
    expect((init as RequestInit).body).toBe(
      JSON.stringify({ bbox: [10, 15, 50, 45], page_hash: 'page_hash_1' })
    );
  });

  it('creates, waits, and reads review resources', async () => {
    const fetchMock = vi
      .fn<Parameters<typeof fetch>, ReturnType<typeof fetch>>()
      .mockResolvedValueOnce(
        jsonResponse({
          review_id: 'rev_1',
          status: 'running',
          total_pages: 1,
          pages: [{ page_number: 13, page_hash: 'page_hash_13', project_id: 'proj_1' }],
        })
      )
      .mockResolvedValueOnce(
        jsonResponse({
          review_id: 'rev_1',
          status: 'completed_partial',
          progress: {
            scout: {
              pending: 0,
              in_progress: 0,
              completed: 1,
              failed: 0,
              total: 1,
            },
            specialist: {
              pending: 0,
              in_progress: 0,
              completed: 3,
              failed: 0,
              out_of_scope: 1,
              total: 4,
              max_turns: 30,
              active: [
                {
                  question_id: 'q_1',
                  agent: 'cross_reference',
                  turns_used: 2,
                  max_turns: 30,
                  updated_at: '2026-03-10T10:05:00Z',
                },
              ],
            },
          },
        })
      )
      .mockResolvedValueOnce(
        jsonResponse({
          review_id: 'rev_1',
          questions: [
            {
              question_id: 'q_1',
              review_id: 'rev_1',
              source: 'scout',
              status: 'completed',
              page_hash: 'page_hash_13',
              project_id: 'proj_1',
              question: 'Check the slab note.',
              assigned_agents: ['cross_reference'],
              raw_model_output: { issues: [], new_questions: [] },
            },
          ],
        })
      )
      .mockResolvedValueOnce(
        jsonResponse({
          review_id: 'rev_1',
          issues: [
            {
              issue_id: 'iss_1',
              review_id: 'rev_1',
              question_id: 'q_1',
              project_id: 'proj_1',
              page_hash: 'page_hash_13',
              agent: 'cross_reference',
              priority: 'P1',
              title: 'Missing referenced section',
              description: 'Callout references a missing section.',
              evidence: ['Detail callout text reads 4/S312.'],
            },
          ],
        })
      );

    vi.stubGlobal('fetch', fetchMock);

    const client = new StruAI({ apiKey: 'k', baseUrl: 'http://localhost:8000' });
    const review = await client.reviews.create({
      fileHash: 'abc123def4567890',
      pages: '13',
      projectIds: ['proj_1'],
      scout:
        'Route broken references to Cross Reference Checker and buildability gaps to Constructability Reviewer.',
      specialistsCommon: 'Shared specialist block',
      specialists: [
        { name: 'Cross Reference Checker', instructions: 'Trace all references.' },
        { name: 'Constructability Reviewer', instructions: 'Review constructability.' },
      ],
      customInstructions: 'Focus on cross-sheet coordination.',
    });

    expect(review.id).toBe('rev_1');
    expect(review.data.pages?.[0]?.page_hash).toBe('page_hash_13');

    const finalReview = await review.wait({ timeoutMs: 1_000, pollIntervalMs: 0 });
    expect(finalReview.is_partial).toBe(true);
    expect(finalReview.progress?.specialist?.max_turns).toBe(30);
    expect(finalReview.progress?.specialist?.active?.[0]?.question_id).toBe('q_1');

    const questions = await review.questions();
    const issues = await review.issues();

    expect(questions[0].raw_model_output).toEqual({ issues: [], new_questions: [] });
    expect(issues[0].priority).toBe('P1');

    const [createUrl, createInit] = fetchMock.mock.calls[0];
    expect(createUrl).toBe('http://localhost:8000/v1/reviews');
    expect((createInit as RequestInit).method).toBe('POST');
    expect((createInit as RequestInit).body).toBe(
      JSON.stringify({
        file_hash: 'abc123def4567890',
        pages: '13',
        project_ids: ['proj_1'],
        scout:
          'Route broken references to Cross Reference Checker and buildability gaps to Constructability Reviewer.',
        specialists_common: 'Shared specialist block',
        specialists: [
          { name: 'Cross Reference Checker', instructions: 'Trace all references.' },
          { name: 'Constructability Reviewer', instructions: 'Review constructability.' },
        ],
        custom_instructions: 'Focus on cross-sheet coordination.',
      })
    );

    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      'http://localhost:8000/v1/reviews',
      'http://localhost:8000/v1/reviews/rev_1',
      'http://localhost:8000/v1/reviews/rev_1/questions',
      'http://localhost:8000/v1/reviews/rev_1/issues',
    ]);
  });

  it('creates a review with multipart upload fields', async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'struai-review-'));
    const pdfPath = path.join(tmpDir, 'sample.pdf');
    await fs.writeFile(pdfPath, Buffer.from('%PDF-1.4\n'));

    const fetchMock = vi
      .fn<Parameters<typeof fetch>, ReturnType<typeof fetch>>()
      .mockResolvedValueOnce(
        jsonResponse({
          review_id: 'rev_upload_1',
          status: 'running',
          total_pages: 1,
          pages: [{ page_number: 13, page_hash: 'page_hash_13', project_id: 'proj_1' }],
        })
      );

    vi.stubGlobal('fetch', fetchMock);

    const client = new StruAI({ apiKey: 'k', baseUrl: 'http://localhost:8000' });
    const review = await client.reviews.create({
      file: pdfPath,
      pages: 13,
      projectIds: ['proj_a', 'proj_b'],
      scout: 'Route all review questions to Cross Reference Checker.',
      specialistsCommon: 'Shared multipart specialist block',
      specialists: [{ name: 'Cross Reference Checker', instructions: 'Trace all references.' }],
      customInstructions: 'Focus on seismic detailing.',
    });

    expect(review.id).toBe('rev_upload_1');

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('http://localhost:8000/v1/reviews');
    expect((init as RequestInit).method).toBe('POST');
    const formData = (init as RequestInit).body as FormData;
    expect(formData.get('pages')).toBe('13');
    expect(formData.getAll('project_ids')).toEqual(['proj_a', 'proj_b']);
    expect(formData.get('scout')).toBe('Route all review questions to Cross Reference Checker.');
    expect(formData.get('specialists_common')).toBe('Shared multipart specialist block');
    expect(formData.get('specialists')).toBe(
      JSON.stringify([{ name: 'Cross Reference Checker', instructions: 'Trace all references.' }])
    );
    expect(formData.get('custom_instructions')).toBe('Focus on seismic detailing.');
    const file = formData.get('file') as File;
    expect(file.name).toBe('sample.pdf');
    expect(file.type).toBe('application/pdf');
  });

  it('rejects duplicate specialist names case-insensitively', async () => {
    const client = new StruAI({ apiKey: 'k', baseUrl: 'http://localhost:8000' });

    await expect(
      client.reviews.create({
        fileHash: 'abc123def4567890',
        pages: '13',
        specialists: [
          { name: 'Cross Reference Checker', instructions: 'Trace all references.' },
          { name: 'cross reference checker', instructions: 'Duplicate name.' },
        ],
      })
    ).rejects.toThrow('specialists names must be unique');
  });

  it('requires scout when specialists are provided', async () => {
    const client = new StruAI({ apiKey: 'k', baseUrl: 'http://localhost:8000' });

    await expect(
      client.reviews.create({
        fileHash: 'abc123def4567890',
        pages: '13',
        specialists: [{ name: 'Cross Reference Checker', instructions: 'Trace all references.' }],
      })
    ).rejects.toThrow('scout is also required');
  });

  it('requires exact specialist names inside scout', async () => {
    const client = new StruAI({ apiKey: 'k', baseUrl: 'http://localhost:8000' });

    await expect(
      client.reviews.create({
        fileHash: 'abc123def4567890',
        pages: '13',
        scout: 'Route broken references to cross reference review.',
        specialists: [{ name: 'Cross Reference Checker', instructions: 'Trace all references.' }],
      })
    ).rejects.toThrow('Missing from scout text');
  });

  it('lists, gets, opens, and fails review wait correctly', async () => {
    const fetchMock = vi
      .fn<Parameters<typeof fetch>, ReturnType<typeof fetch>>()
      .mockResolvedValueOnce(
        jsonResponse({
          reviews: [{ review_id: 'rev_list_1', status: 'completed', file_hash: 'file_hash_1' }],
        })
      )
      .mockResolvedValueOnce(jsonResponse({ review_id: 'rev_1', status: 'failed' }))
      .mockResolvedValueOnce(jsonResponse({ review_id: 'rev_2', status: 'failed' }));

    vi.stubGlobal('fetch', fetchMock);

    const client = new StruAI({ apiKey: 'k', baseUrl: 'http://localhost:8000' });

    const listed = await client.reviews.list({ status: 'completed' });
    expect(listed[0].review_id).toBe('rev_list_1');
    expect(listed[0].is_complete).toBe(true);

    const fetched = await client.reviews.get('rev_1');
    expect(fetched.id).toBe('rev_1');
    expect(fetched.data.is_failed).toBe(true);

    const failedReview = client.reviews.open('rev_2');
    await expect(failedReview.wait({ timeoutMs: 1_000, pollIntervalMs: 0 })).rejects.toThrow(
      'Review rev_2 failed'
    );
  });
});
