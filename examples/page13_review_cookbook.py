#!/usr/bin/env python3
"""End-to-end Page 13 review cookbook for the Python SDK."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, TypeVar

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from struai import APIError, ReviewFailedError, StruAI, TimeoutError  # noqa: E402
from struai.models.reviews import (  # noqa: E402
    Review,
    ReviewActiveSpecialist,
    ReviewIssue,
    ReviewQuestion,
)

T = TypeVar("T")


def _env_required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def _parse_project_ids(raw: str) -> List[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


def _read_optional_text_file(path_str: str | None, *, label: str) -> Optional[str]:
    if not path_str:
        return None
    path = Path(path_str)
    if not path.exists():
        raise SystemExit(f"{label} file not found: {path}")
    text = path.read_text().strip()
    return text or None


def _read_specialists_file(path_str: str | None) -> Optional[List[Dict[str, Any]]]:
    if not path_str:
        return None
    path = Path(path_str)
    if not path.exists():
        raise SystemExit(f"specialists file not found: {path}")
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise SystemExit(f"specialists file is not valid JSON: {exc}") from exc
    if not isinstance(payload, list):
        raise SystemExit("specialists file must contain a JSON array")
    return payload


def _iso(value) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _render_active(active: Iterable[ReviewActiveSpecialist]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for item in active:
        rows.append(
            {
                "question_id": item.question_id,
                "agent": item.agent,
                "turns_used": item.turns_used,
                "max_turns": item.max_turns,
                "updated_at": _iso(item.updated_at),
            }
        )
    return rows


def _print_json(label: str, payload: object) -> None:
    print(f"{label}={json.dumps(payload, indent=2, default=str)}")


def _is_transient(exc: APIError) -> bool:
    if exc.status_code in {500, 502, 503, 504}:
        return True
    return str(exc.code or "").lower() in {
        "drawing_warming_up",
        "drawing_unavailable",
        "internal_error",
    }


def _call_with_retry(fn: Callable[[], T], *, label: str, attempts: int = 4) -> T:
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except APIError as exc:
            if _is_transient(exc) and attempt < attempts:
                wait_s = min(2 ** (attempt - 1), 8)
                retry_info = {
                    "attempt": attempt,
                    "wait_s": wait_s,
                    "status": exc.status_code,
                    "code": exc.code,
                }
                print(f"{label}_retry={json.dumps(retry_info)}")
                time.sleep(wait_s)
                continue
            raise
    raise RuntimeError(f"{label} failed after retries")


def _snapshot(label: str, review: Review, *, elapsed_s: float) -> None:
    progress = review.progress.model_dump() if review.progress else None
    payload = {
        "review_id": review.review_id,
        "status": review.status,
        "elapsed_s": round(elapsed_s, 1),
        "total_pages": review.total_pages,
        "page_selector": review.page_selector,
        "pages": [page.model_dump() for page in review.pages],
        "progress": progress,
    }
    _print_json(label, payload)


def _question_summary(question: ReviewQuestion) -> Dict[str, object]:
    return {
        "question_id": question.question_id,
        "source": question.source,
        "status": question.status,
        "agent": question.assigned_agents[0] if question.assigned_agents else None,
        "turns_used": question.turns_used,
        "question": question.question,
        "error": question.error,
    }


def _issue_summary(issue: ReviewIssue) -> Dict[str, object]:
    return {
        "issue_id": issue.issue_id,
        "question_id": issue.question_id,
        "agent": issue.agent,
        "priority": issue.priority,
        "title": issue.title,
    }


def main() -> int:
    load_dotenv(REPO_ROOT / ".env")

    api_key = _env_required("STRUAI_API_KEY")
    base_url = os.environ.get("STRUAI_BASE_URL", "https://api.stru.ai").strip()
    file_hash = _env_required("STRUAI_REVIEW_FILE_HASH")
    pages = os.environ.get("STRUAI_REVIEW_PAGES", "13").strip()
    project_ids = _parse_project_ids(os.environ.get("STRUAI_REVIEW_PROJECT_IDS", ""))
    timeout_s = float(os.environ.get("STRUAI_REVIEW_TIMEOUT", "2100"))
    poll_interval_s = float(os.environ.get("STRUAI_REVIEW_POLL_INTERVAL", "10"))
    custom_instructions = os.environ.get("STRUAI_REVIEW_CUSTOM_INSTRUCTIONS", "").strip() or None
    scout = _read_optional_text_file(
        os.environ.get("STRUAI_REVIEW_SCOUT_FILE"),
        label="scout",
    )
    specialists_common = _read_optional_text_file(
        os.environ.get("STRUAI_REVIEW_SPECIALISTS_COMMON_FILE"),
        label="specialists_common",
    )
    specialists = _read_specialists_file(os.environ.get("STRUAI_REVIEW_SPECIALISTS_FILE"))

    client = StruAI(api_key=api_key, base_url=base_url)

    start_ts = time.time()
    _print_json(
        "prompt_config",
        {
            "mode": "custom" if any([scout, specialists_common, specialists]) else "default",
            "scout_file": os.environ.get("STRUAI_REVIEW_SCOUT_FILE"),
            "specialists_common_file": os.environ.get("STRUAI_REVIEW_SPECIALISTS_COMMON_FILE"),
            "specialists_file": os.environ.get("STRUAI_REVIEW_SPECIALISTS_FILE"),
            "specialists_count": len(specialists or []),
        },
    )
    review_handle = _call_with_retry(
        lambda: client.reviews.create(
            file_hash=file_hash,
            pages=pages,
            project_ids=project_ids or None,
            scout=scout,
            specialists_common=specialists_common,
            specialists=specialists,
            custom_instructions=custom_instructions,
        ),
        label="create_review",
    )
    created = review_handle.data
    _snapshot("create", created, elapsed_s=time.time() - start_ts)

    listed = _call_with_retry(client.reviews.list, label="list_reviews")
    matching = [review.review_id for review in listed if review.review_id == review_handle.id]
    _print_json(
        "list_check",
        {
            "review_id": review_handle.id,
            "seen_in_list": bool(matching),
            "list_count": len(listed),
        },
    )

    fetched = _call_with_retry(
        lambda: client.reviews.get(review_handle.id).data, label="get_review"
    )
    _snapshot("get", fetched, elapsed_s=time.time() - start_ts)

    history_handle = client.reviews.open(review_handle.id)
    _snapshot(
        "open_initial",
        _call_with_retry(history_handle.refresh, label="open_refresh"),
        elapsed_s=time.time() - start_ts,
    )

    last_question_count = -1
    last_issue_count = -1
    poll_count = 0

    while True:
        poll_count += 1
        current = _call_with_retry(review_handle.refresh, label="refresh_review")
        elapsed_s = time.time() - start_ts
        active = (
            current.progress.specialist.active
            if current.progress and current.progress.specialist
            else []
        )
        _print_json(
            "status_poll",
            {
                "poll": poll_count,
                "review_id": current.review_id,
                "status": current.status,
                "elapsed_s": round(elapsed_s, 1),
                "scout": current.progress.scout.model_dump()
                if current.progress and current.progress.scout
                else None,
                "specialist": current.progress.specialist.model_dump()
                if current.progress and current.progress.specialist
                else None,
                "active_specialists": _render_active(active),
            },
        )

        questions = _call_with_retry(review_handle.questions, label="get_questions")
        issues = _call_with_retry(review_handle.issues, label="get_issues")
        if len(questions) != last_question_count:
            last_question_count = len(questions)
            _print_json(
                "questions_snapshot",
                {
                    "count": len(questions),
                    "items": [_question_summary(question) for question in questions[:5]],
                },
            )
        if len(issues) != last_issue_count:
            last_issue_count = len(issues)
            _print_json(
                "issues_snapshot",
                {
                    "count": len(issues),
                    "items": [_issue_summary(issue) for issue in issues[:5]],
                },
            )

        if current.is_terminal:
            break
        if elapsed_s >= timeout_s:
            raise TimeoutError(f"Review {review_handle.id} did not complete within {timeout_s}s")
        time.sleep(poll_interval_s)

    final_review = review_handle.data
    _snapshot("final", final_review, elapsed_s=time.time() - start_ts)

    final_questions = _call_with_retry(review_handle.questions, label="final_questions")
    final_issues = _call_with_retry(review_handle.issues, label="final_issues")
    agent_turns = [
        {
            "question_id": question.question_id,
            "agent": question.assigned_agents[0] if question.assigned_agents else None,
            "status": question.status,
            "turns_used": question.turns_used,
        }
        for question in final_questions
    ]
    turn_values = [
        item["turns_used"] for item in agent_turns if isinstance(item["turns_used"], int)
    ]
    stats = {
        "review_id": review_handle.id,
        "status": final_review.status,
        "elapsed_s": round(time.time() - start_ts, 1),
        "question_count": len(final_questions),
        "issue_count": len(final_issues),
        "turn_stats": {
            "count": len(turn_values),
            "min": min(turn_values) if turn_values else None,
            "max": max(turn_values) if turn_values else None,
            "avg": round(sum(turn_values) / len(turn_values), 2) if turn_values else None,
        },
        "agents": agent_turns,
    }
    _print_json("stats", stats)

    historical = _call_with_retry(
        lambda: client.reviews.get(review_handle.id), label="historical_get"
    )
    _snapshot("historical_get", historical.data, elapsed_s=time.time() - start_ts)
    historical_questions = _call_with_retry(historical.questions, label="historical_questions")
    historical_issues = _call_with_retry(historical.issues, label="historical_issues")
    _print_json(
        "historical_questions",
        {
            "count": len(historical_questions),
            "items": [_question_summary(question) for question in historical_questions[:5]],
        },
    )
    _print_json(
        "historical_issues",
        {
            "count": len(historical_issues),
            "items": [_issue_summary(issue) for issue in historical_issues[:5]],
        },
    )

    if final_review.is_failed:
        raise ReviewFailedError(f"Review {review_handle.id} failed", review_id=review_handle.id)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
