"""Review system resource."""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from .._exceptions import ReviewFailedError, TimeoutError
from ..models.reviews import (
    Review,
    ReviewIssue,
    ReviewIssuesResult,
    ReviewListResponse,
    ReviewQuestion,
    ReviewQuestionsResult,
)
from ._uploads import Uploadable, _prepare_file

if TYPE_CHECKING:
    from .._base import AsyncBaseClient, BaseClient


def _normalize_pages(pages: Union[int, str]) -> str:
    if isinstance(pages, int):
        return str(pages)
    text = str(pages).strip()
    if not text:
        raise ValueError("pages is required")
    return text


def _normalize_text(value: Any, *, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required")
    return text


def _normalize_optional_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_specialists(
    specialists: Optional[List[Dict[str, Any]]],
) -> Optional[List[Dict[str, str]]]:
    if specialists is None:
        return None
    if not specialists:
        raise ValueError("specialists cannot be empty")

    normalized: List[Dict[str, str]] = []
    seen: Dict[str, str] = {}
    for specialist in specialists:
        if hasattr(specialist, "model_dump"):
            specialist = specialist.model_dump()
        if not isinstance(specialist, dict):
            raise ValueError("specialists must be a list of objects with name and instructions")

        name = _normalize_text(specialist.get("name"), field_name="specialists[].name")
        instructions = _normalize_text(
            specialist.get("instructions"),
            field_name="specialists[].instructions",
        )
        folded = name.casefold()
        prior = seen.get(folded)
        if prior is not None:
            raise ValueError(
                "specialists names must be unique within the request: "
                f"'{name}' duplicates '{prior}'"
            )
        seen[folded] = name
        normalized.append({"name": name, "instructions": instructions})
    return normalized


def _multipart_form_fields(
    *,
    pages: str,
    project_ids: Optional[List[str]],
    scout: Optional[str],
    specialists_common: Optional[str],
    specialists: Optional[List[Dict[str, str]]],
    custom_instructions: Optional[str],
) -> List[Tuple[str, str]]:
    fields: List[Tuple[str, str]] = [("pages", pages)]
    for project_id in project_ids or []:
        clean_project_id = str(project_id).strip()
        if clean_project_id:
            fields.append(("project_ids", clean_project_id))
    if scout is not None:
        fields.append(("scout", scout))
    if specialists_common is not None:
        fields.append(("specialists_common", specialists_common))
    if specialists is not None:
        fields.append(("specialists", json.dumps(specialists, ensure_ascii=True)))
    if custom_instructions is not None:
        fields.append(("custom_instructions", custom_instructions))
    return fields


class ReviewInstance:
    """Handle for one review (sync)."""

    def __init__(self, client: "BaseClient", review: Review):
        self._client = client
        self._review = review

    @property
    def id(self) -> str:
        return self._review.review_id

    @property
    def data(self) -> Review:
        return self._review

    def refresh(self) -> Review:
        """Fetch the latest review state."""
        self._review = self._client.get(f"/reviews/{self.id}", cast_to=Review)
        return self._review

    def status(self) -> Review:
        """Alias for refresh()."""
        return self.refresh()

    def questions(self) -> List[ReviewQuestion]:
        """Fetch all persisted questions for this review."""
        result = self._client.get(f"/reviews/{self.id}/questions", cast_to=ReviewQuestionsResult)
        return result.questions

    def issues(self) -> List[ReviewIssue]:
        """Fetch all persisted issues for this review."""
        result = self._client.get(f"/reviews/{self.id}/issues", cast_to=ReviewIssuesResult)
        return result.issues

    def wait(self, timeout: float = 900, poll_interval: float = 5) -> Review:
        """Wait for the review to reach a terminal state."""
        start = time.time()
        latest = self._review
        while time.time() - start < timeout:
            if latest.is_failed:
                raise ReviewFailedError(f"Review {self.id} failed", review_id=self.id)
            if latest.is_terminal:
                self._review = latest
                return latest
            time.sleep(poll_interval)
            latest = self.refresh()
        raise TimeoutError(f"Review {self.id} did not complete within {timeout}s")


class AsyncReviewInstance:
    """Handle for one review (async)."""

    def __init__(self, client: "AsyncBaseClient", review: Review):
        self._client = client
        self._review = review

    @property
    def id(self) -> str:
        return self._review.review_id

    @property
    def data(self) -> Review:
        return self._review

    async def refresh(self) -> Review:
        """Fetch the latest review state."""
        self._review = await self._client.get(f"/reviews/{self.id}", cast_to=Review)
        return self._review

    async def status(self) -> Review:
        """Alias for refresh()."""
        return await self.refresh()

    async def questions(self) -> List[ReviewQuestion]:
        """Fetch all persisted questions for this review."""
        result = await self._client.get(
            f"/reviews/{self.id}/questions",
            cast_to=ReviewQuestionsResult,
        )
        return result.questions

    async def issues(self) -> List[ReviewIssue]:
        """Fetch all persisted issues for this review."""
        result = await self._client.get(
            f"/reviews/{self.id}/issues",
            cast_to=ReviewIssuesResult,
        )
        return result.issues

    async def wait(self, timeout: float = 900, poll_interval: float = 5) -> Review:
        """Wait for the review to reach a terminal state."""
        import asyncio

        start = time.time()
        latest = self._review
        while time.time() - start < timeout:
            if latest.is_failed:
                raise ReviewFailedError(f"Review {self.id} failed", review_id=self.id)
            if latest.is_terminal:
                self._review = latest
                return latest
            await asyncio.sleep(poll_interval)
            latest = await self.refresh()
        raise TimeoutError(f"Review {self.id} did not complete within {timeout}s")


class Reviews:
    """Top-level reviews API (sync)."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def create(
        self,
        *,
        pages: Union[int, str],
        file: Optional[Uploadable] = None,
        file_hash: Optional[str] = None,
        project_ids: Optional[List[str]] = None,
        scout: Optional[str] = None,
        specialists_common: Optional[str] = None,
        specialists: Optional[List[Dict[str, Any]]] = None,
        custom_instructions: Optional[str] = None,
    ) -> ReviewInstance:
        """Create a review via file_hash JSON or multipart PDF upload."""
        page_selector = _normalize_pages(pages)
        scout = _normalize_optional_text(scout)
        specialists_common = _normalize_optional_text(specialists_common)
        specialists = _normalize_specialists(specialists)
        custom_instructions = _normalize_optional_text(custom_instructions)
        if file is None and not file_hash:
            raise ValueError("Provide file or file_hash")
        if file is not None and file_hash:
            raise ValueError("Provide either file or file_hash, not both")

        if file_hash:
            review = self._client.post(
                "/reviews",
                json={
                    "file_hash": file_hash,
                    "pages": page_selector,
                    "project_ids": project_ids,
                    "scout": scout,
                    "specialists_common": specialists_common,
                    "specialists": specialists,
                    "custom_instructions": custom_instructions,
                },
                cast_to=Review,
            )
            return ReviewInstance(self._client, review)

        upload = None
        handle = None
        try:
            upload, handle = _prepare_file(file)
            review = self._client.post(
                "/reviews",
                files=upload,
                data=_multipart_form_fields(
                    pages=page_selector,
                    project_ids=project_ids,
                    scout=scout,
                    specialists_common=specialists_common,
                    specialists=specialists,
                    custom_instructions=custom_instructions,
                ),
                cast_to=Review,
            )
            return ReviewInstance(self._client, review)
        finally:
            if handle is not None:
                handle.close()

    def list(self, *, status: Optional[str] = None) -> List[Review]:
        """List reviews available to the API key."""
        result = self._client.get(
            "/reviews",
            params={"status": status} if status else None,
            cast_to=ReviewListResponse,
        )
        return result.reviews

    def get(self, review_id: str) -> ReviewInstance:
        """Fetch one review and return a handle."""
        clean_review_id = _normalize_text(review_id, field_name="review_id")
        review = self._client.get(f"/reviews/{clean_review_id}", cast_to=Review)
        return ReviewInstance(self._client, review)

    def open(self, review_id: str) -> ReviewInstance:
        """Create a review handle without performing a lookup call."""
        clean_review_id = _normalize_text(review_id, field_name="review_id")
        review = Review.model_validate({"review_id": clean_review_id})
        return ReviewInstance(self._client, review)


class AsyncReviews:
    """Top-level reviews API (async)."""

    def __init__(self, client: "AsyncBaseClient"):
        self._client = client

    async def create(
        self,
        *,
        pages: Union[int, str],
        file: Optional[Uploadable] = None,
        file_hash: Optional[str] = None,
        project_ids: Optional[List[str]] = None,
        scout: Optional[str] = None,
        specialists_common: Optional[str] = None,
        specialists: Optional[List[Dict[str, Any]]] = None,
        custom_instructions: Optional[str] = None,
    ) -> AsyncReviewInstance:
        """Create a review via file_hash JSON or multipart PDF upload."""
        page_selector = _normalize_pages(pages)
        scout = _normalize_optional_text(scout)
        specialists_common = _normalize_optional_text(specialists_common)
        specialists = _normalize_specialists(specialists)
        custom_instructions = _normalize_optional_text(custom_instructions)
        if file is None and not file_hash:
            raise ValueError("Provide file or file_hash")
        if file is not None and file_hash:
            raise ValueError("Provide either file or file_hash, not both")

        if file_hash:
            review = await self._client.post(
                "/reviews",
                json={
                    "file_hash": file_hash,
                    "pages": page_selector,
                    "project_ids": project_ids,
                    "scout": scout,
                    "specialists_common": specialists_common,
                    "specialists": specialists,
                    "custom_instructions": custom_instructions,
                },
                cast_to=Review,
            )
            return AsyncReviewInstance(self._client, review)

        upload = None
        handle = None
        try:
            upload, handle = _prepare_file(file)
            review = await self._client.post(
                "/reviews",
                files=upload,
                data=_multipart_form_fields(
                    pages=page_selector,
                    project_ids=project_ids,
                    scout=scout,
                    specialists_common=specialists_common,
                    specialists=specialists,
                    custom_instructions=custom_instructions,
                ),
                cast_to=Review,
            )
            return AsyncReviewInstance(self._client, review)
        finally:
            if handle is not None:
                handle.close()

    async def list(self, *, status: Optional[str] = None) -> List[Review]:
        """List reviews available to the API key."""
        result = await self._client.get(
            "/reviews",
            params={"status": status} if status else None,
            cast_to=ReviewListResponse,
        )
        return result.reviews

    async def get(self, review_id: str) -> AsyncReviewInstance:
        """Fetch one review and return a handle."""
        clean_review_id = _normalize_text(review_id, field_name="review_id")
        review = await self._client.get(f"/reviews/{clean_review_id}", cast_to=Review)
        return AsyncReviewInstance(self._client, review)

    def open(self, review_id: str) -> AsyncReviewInstance:
        """Create a review handle without performing a lookup call."""
        clean_review_id = _normalize_text(review_id, field_name="review_id")
        review = Review.model_validate({"review_id": clean_review_id})
        return AsyncReviewInstance(self._client, review)


__all__ = [
    "Reviews",
    "AsyncReviews",
    "ReviewInstance",
    "AsyncReviewInstance",
]
