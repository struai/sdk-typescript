"""Local smoke test for StruAI Python SDK.

Usage:
  STRUAI_API_KEY=YOUR_API_KEY STRUAI_BASE_URL=http://localhost:8000 \
    python3 scripts/smoke_local.py

Optional:
  STRUAI_PDF=/path/to.pdf STRUAI_PAGE=12   # ingest sheet(s)
  STRUAI_SEARCH="GB18x18"                 # run docquery search
  STRUAI_REVIEW_FILE_HASH=abc123...       # start a review by existing file_hash
  STRUAI_REVIEW_PAGES=13                  # page selector for review
  STRUAI_REVIEW_PROJECT_IDS=proj_1,proj_2 # optional CSV project ids
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from struai import StruAI  # noqa: E402
from struai.resources.projects import JobBatch  # noqa: E402


def _wait_ingest(result_or_batch):
    if isinstance(result_or_batch, JobBatch):
        return result_or_batch.wait_all(timeout_per_job=300)
    return [result_or_batch.wait(timeout=300)]


def main() -> None:
    base_url = os.getenv("STRUAI_BASE_URL", "http://localhost:8000")
    api_key = os.getenv("STRUAI_API_KEY")
    if not api_key:
        raise SystemExit("Missing STRUAI_API_KEY")
    client = StruAI(api_key=api_key, base_url=base_url)

    projects = client.projects.list()
    if projects:
        project = client.projects.open(projects[0].id, name=projects[0].name)
        created = False
    else:
        project = client.projects.create(name="Smoke Test Project")
        created = True

    sheet_list = project.docquery.sheet_list()
    print(
        f"project={project.id} "
        f"sheet_nodes={sheet_list.totals.get('sheet_node_count', 0)} "
        f"mismatches={len(sheet_list.mismatch_warnings)}"
    )

    pdf_path = os.getenv("STRUAI_PDF")
    if pdf_path:
        page = os.getenv("STRUAI_PAGE", "1")
        ingest = project.sheets.add(pdf_path, page=page)
        results = _wait_ingest(ingest)
        print(f"ingested_jobs={len(results)} first_sheet_id={results[0].sheet_id}")

    search_query = os.getenv("STRUAI_SEARCH")
    if search_query:
        results = project.docquery.search(query=search_query, limit=3)
        print(f"search_count={len(results.hits)}")

    review_file_hash = os.getenv("STRUAI_REVIEW_FILE_HASH")
    if review_file_hash:
        review_pages = os.getenv("STRUAI_REVIEW_PAGES", "13")
        review_project_ids = [
            project_id.strip()
            for project_id in os.getenv("STRUAI_REVIEW_PROJECT_IDS", "").split(",")
            if project_id.strip()
        ]
        review = client.reviews.create(
            file_hash=review_file_hash,
            pages=review_pages,
            project_ids=review_project_ids or None,
        )
        latest = review.refresh()
        specialist = latest.progress.specialist if latest.progress else None
        print(
            f"review_id={review.id} status={latest.status} "
            f"specialist_total={getattr(specialist, 'total', 0)} "
            f"specialist_active={len(getattr(specialist, 'active', []) or [])}"
        )

    if created:
        project.delete()


if __name__ == "__main__":
    main()
