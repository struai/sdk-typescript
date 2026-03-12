from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Optional

import pytest

from struai import ReviewFailedError, TimeoutError
from struai.resources.reviews import AsyncReviewInstance, AsyncReviews, ReviewInstance, Reviews


def _create_payload(review_id: str = "rev_1", status: str = "running") -> dict[str, Any]:
    return {
        "review_id": review_id,
        "status": status,
        "total_pages": 1,
        "pages": [
            {
                "page_number": 13,
                "page_hash": "page_hash_13",
                "project_id": "proj_1",
            }
        ],
    }


class FakeReviewClient:
    def __init__(self, *, status_sequence: Optional[list[str]] = None) -> None:
        self.posts: list[dict[str, Any]] = []
        self.gets: list[dict[str, Any]] = []
        self._status_sequence = status_sequence or ["running", "completed_partial"]
        self._status_calls = 0

    def post(self, path: str, *, files=None, data=None, json=None, cast_to=None):
        self.posts.append({"path": path, "files": files, "data": data, "json": json})
        payload = _create_payload()
        return cast_to.model_validate(payload) if cast_to else payload

    def get(self, path: str, params: Optional[dict[str, Any]] = None, cast_to=None):
        self.gets.append({"path": path, "params": params})

        if path == "/reviews":
            payload = {
                "reviews": [
                    {
                        "review_id": "rev_list_1",
                        "status": "completed",
                        "file_hash": "file_hash_1",
                        "page_selector": "13",
                    }
                ]
            }
        elif path == "/reviews/rev_1":
            status = self._status_sequence[min(self._status_calls, len(self._status_sequence) - 1)]
            self._status_calls += 1
            payload = {
                "review_id": "rev_1",
                "status": status,
                "created_at": "2026-03-10T10:00:00Z",
                "completed_at": None if status == "running" else "2026-03-10T10:15:00Z",
                "file_hash": "file_hash_1",
                "custom_instructions": "Focus on coordination",
                "progress": {
                    "scout": {
                        "pending": 0,
                        "in_progress": 0,
                        "completed": 1,
                        "failed": 0,
                        "total": 1,
                    },
                    "specialist": {
                        "pending": 0,
                        "in_progress": 0,
                        "completed": 3,
                        "failed": 0,
                        "out_of_scope": 1,
                        "total": 4,
                        "max_turns": 30,
                        "active": [
                            {
                                "question_id": "q_active_1",
                                "agent": "cross_reference",
                                "turns_used": 2,
                                "max_turns": 30,
                                "updated_at": "2026-03-10T10:05:00Z",
                            }
                        ],
                    },
                },
            }
        elif path == "/reviews/rev_1/questions":
            payload = {
                "review_id": "rev_1",
                "questions": [
                    {
                        "question_id": "q_1",
                        "review_id": "rev_1",
                        "review_page_id": "rp_1",
                        "source": "scout",
                        "status": "completed",
                        "page_hash": "page_hash_13",
                        "project_id": "proj_1",
                        "question": "Check the slab note.",
                        "location_description": "north edge",
                        "assigned_agents": ["cross_reference"],
                        "raw_model_output": {
                            "issues": [],
                            "new_questions": [
                                {
                                    "question": "Follow up",
                                    "assigned_agent": "cross_reference",
                                }
                            ],
                        },
                    }
                ],
            }
        elif path == "/reviews/rev_1/issues":
            payload = {
                "review_id": "rev_1",
                "issues": [
                    {
                        "issue_id": "iss_1",
                        "review_id": "rev_1",
                        "question_id": "q_1",
                        "project_id": "proj_1",
                        "page_hash": "page_hash_13",
                        "agent": "cross_reference",
                        "priority": "P1",
                        "category": "missing_info",
                        "title": "Missing referenced section",
                        "description": "Callout references a missing section.",
                        "evidence": ["Detail callout text reads 4/S312."],
                        "suggested_fix": "Correct the callout.",
                    }
                ],
            }
        else:
            raise AssertionError(f"unexpected GET {path}")

        return cast_to.model_validate(payload) if cast_to else payload


class FakeAsyncReviewClient(FakeReviewClient):
    async def post(self, path: str, *, files=None, data=None, json=None, cast_to=None):
        return super().post(path, files=files, data=data, json=json, cast_to=cast_to)

    async def get(self, path: str, params: Optional[dict[str, Any]] = None, cast_to=None):
        return super().get(path, params=params, cast_to=cast_to)


def test_reviews_create_with_file_hash_posts_json_and_returns_handle() -> None:
    client = FakeReviewClient()
    reviews = Reviews(client)

    review = reviews.create(
        pages="12,13",
        file_hash="abc123",
        project_ids=["proj_1"],
        custom_instructions="Focus on lateral coordination",
    )

    assert isinstance(review, ReviewInstance)
    assert review.id == "rev_1"
    assert review.data.total_pages == 1
    assert review.data.pages[0].page_hash == "page_hash_13"

    assert len(client.posts) == 1
    request = client.posts[0]
    assert request["path"] == "/reviews"
    assert request["json"] == {
        "file_hash": "abc123",
        "pages": "12,13",
        "project_ids": ["proj_1"],
        "custom_instructions": "Focus on lateral coordination",
    }
    assert request["files"] is None


def test_reviews_create_with_file_upload_posts_multipart_fields(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")

    client = FakeReviewClient()
    reviews = Reviews(client)

    review = reviews.create(
        pages=13,
        file=pdf_path,
        project_ids=["proj_a", "proj_b"],
        custom_instructions="Focus on seismic detailing",
    )

    assert review.id == "rev_1"

    request = client.posts[0]
    assert request["json"] is None
    assert request["data"] == [
        ("pages", "13"),
        ("project_ids", "proj_a"),
        ("project_ids", "proj_b"),
        ("custom_instructions", "Focus on seismic detailing"),
    ]
    assert request["files"]["file"][0] == "sample.pdf"
    assert request["files"]["file"][2] == "application/pdf"
    assert request["files"]["file"][1].closed is True


def test_review_wait_questions_and_issues_use_expected_endpoints() -> None:
    client = FakeReviewClient()
    review = Reviews(client).open("rev_1")

    final = review.wait(timeout=1, poll_interval=0)
    assert final.is_partial
    assert final.progress is not None
    assert final.progress.specialist is not None
    assert final.progress.specialist.out_of_scope == 1
    assert final.progress.specialist.max_turns == 30
    assert len(final.progress.specialist.active) == 1
    assert final.progress.specialist.active[0].question_id == "q_active_1"
    assert final.progress.specialist.active[0].agent == "cross_reference"

    questions = review.questions()
    issues = review.issues()

    assert len(questions) == 1
    assert questions[0].assigned_agents == ["cross_reference"]
    assert isinstance(questions[0].raw_model_output, dict)
    assert questions[0].raw_model_output["issues"] == []
    assert len(issues) == 1
    assert issues[0].priority == "P1"

    paths = [call["path"] for call in client.gets]
    assert paths == [
        "/reviews/rev_1",
        "/reviews/rev_1",
        "/reviews/rev_1/questions",
        "/reviews/rev_1/issues",
    ]


def test_reviews_list_and_get_return_review_models() -> None:
    client = FakeReviewClient()
    reviews = Reviews(client)

    listed = reviews.list(status="completed")
    fetched = reviews.get("rev_1")

    assert len(listed) == 1
    assert listed[0].review_id == "rev_list_1"
    assert listed[0].is_complete
    assert fetched.id == "rev_1"
    assert client.gets[0] == {"path": "/reviews", "params": {"status": "completed"}}


def test_review_wait_raises_on_failed_status() -> None:
    client = FakeReviewClient(status_sequence=["running", "failed"])
    review = Reviews(client).open("rev_1")

    with pytest.raises(ReviewFailedError, match="Review rev_1 failed"):
        review.wait(timeout=1, poll_interval=0)


def test_review_wait_raises_timeout_when_never_terminal() -> None:
    client = FakeReviewClient(status_sequence=["running"])
    review = Reviews(client).open("rev_1")

    with pytest.raises(TimeoutError, match="Review rev_1 did not complete"):
        review.wait(timeout=0.001, poll_interval=0)


def test_reviews_create_validates_input_and_accepts_binary_io() -> None:
    client = FakeReviewClient()
    reviews = Reviews(client)

    with pytest.raises(ValueError, match="Provide file or file_hash"):
        reviews.create(pages=13)

    with pytest.raises(ValueError, match="Provide either file or file_hash, not both"):
        reviews.create(pages=13, file=b"%PDF", file_hash="abc123")

    handle = io.BytesIO(b"%PDF-1.4\n")
    handle.name = "memory.pdf"  # type: ignore[attr-defined]

    review = reviews.create(pages=13, file=handle)
    assert review.id == "rev_1"
    assert client.posts[0]["files"]["file"][1] is handle
    assert handle.closed is False


@pytest.mark.asyncio
async def test_async_reviews_create_wait_and_read_methods() -> None:
    client = FakeAsyncReviewClient()
    reviews = AsyncReviews(client)

    review = await reviews.create(
        pages="12,13",
        file_hash="abc123",
        project_ids=["proj_1"],
        custom_instructions="Focus on lateral coordination",
    )

    assert isinstance(review, AsyncReviewInstance)
    final = await review.wait(timeout=1, poll_interval=0)
    questions = await review.questions()
    issues = await review.issues()

    assert final.is_partial
    assert len(questions) == 1
    assert isinstance(questions[0].raw_model_output, dict)
    assert len(issues) == 1


@pytest.mark.asyncio
async def test_async_review_wait_raises_on_failed_status() -> None:
    client = FakeAsyncReviewClient(status_sequence=["running", "failed"])
    review = AsyncReviews(client).open("rev_1")

    with pytest.raises(ReviewFailedError, match="Review rev_1 failed"):
        await review.wait(timeout=1, poll_interval=0)
