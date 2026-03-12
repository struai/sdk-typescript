#!/usr/bin/env python3
"""Portable review workflow example for StruAI."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import List, Optional

from struai import ReviewFailedError, StruAI, TimeoutError


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start and optionally wait on a StruAI review")
    parser.add_argument(
        "--pdf",
        default=os.environ.get("STRUAI_PDF"),
        help="Path to source PDF for multipart upload review creation",
    )
    parser.add_argument(
        "--file-hash",
        default=os.environ.get("STRUAI_REVIEW_FILE_HASH"),
        help="Existing drawing file_hash to review",
    )
    parser.add_argument(
        "--pages",
        default=os.environ.get("STRUAI_REVIEW_PAGES", os.environ.get("STRUAI_PAGE", "13")),
        help="Review page selector (for example: 13, 12-16, all)",
    )
    parser.add_argument(
        "--project-ids",
        default=os.environ.get("STRUAI_REVIEW_PROJECT_IDS", ""),
        help="Comma-separated project ids to constrain review context",
    )
    parser.add_argument(
        "--custom-instructions",
        default=os.environ.get("STRUAI_REVIEW_CUSTOM_INSTRUCTIONS"),
        help="Optional extra review instructions",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("STRUAI_API_KEY"),
        help="API key (or set STRUAI_API_KEY)",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("STRUAI_BASE_URL", "https://api.stru.ai"),
        help="Base URL (SDK appends /v1 automatically when needed)",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for terminal review status and fetch persisted questions/issues",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.environ.get("STRUAI_REVIEW_TIMEOUT", "900")),
        help="Review wait timeout seconds",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=float(os.environ.get("STRUAI_REVIEW_POLL_INTERVAL", "5")),
        help="Review wait poll interval seconds",
    )
    return parser.parse_args()


def _parse_project_ids(raw: str) -> Optional[List[str]]:
    values = [value.strip() for value in raw.split(",") if value.strip()]
    return values or None


def _print_review(label: str, review) -> None:
    payload = {
        "review_id": review.review_id,
        "status": review.status,
        "total_pages": review.total_pages,
        "pages": [page.model_dump() for page in review.pages],
        "progress": review.progress.model_dump() if review.progress else None,
    }
    print(f"{label}={json.dumps(payload, indent=2, default=str)}")


def main() -> int:
    args = _parse_args()

    if not args.api_key:
        print("Missing API key. Pass --api-key or set STRUAI_API_KEY.")
        return 1

    if not args.file_hash and not args.pdf:
        print("Provide --file-hash or --pdf.")
        return 1

    pdf_path: Optional[Path] = None
    if args.pdf:
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            print(f"PDF not found: {pdf_path}")
            return 1

    client = StruAI(api_key=args.api_key, base_url=args.base_url)
    project_ids = _parse_project_ids(args.project_ids)

    if args.file_hash:
        review = client.reviews.create(
            file_hash=args.file_hash,
            pages=args.pages,
            project_ids=project_ids,
            custom_instructions=args.custom_instructions,
        )
    else:
        review = client.reviews.create(
            file=str(pdf_path),
            pages=args.pages,
            project_ids=project_ids,
            custom_instructions=args.custom_instructions,
        )

    _print_review("created_review", review.data)

    refreshed = review.refresh()
    _print_review("refreshed_review", refreshed)

    if not args.wait:
        return 0

    try:
        final = review.wait(timeout=args.timeout, poll_interval=args.poll_interval)
    except ReviewFailedError as exc:
        print(f"review_failed review_id={exc.review_id}")
        return 2
    except TimeoutError:
        print(f"review_timeout review_id={review.id}")
        return 3

    _print_review("final_review", final)
    questions = review.questions()
    issues = review.issues()
    print(f"review_counts review_id={review.id} questions={len(questions)} issues={len(issues)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
