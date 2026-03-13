"""Review system models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import Field

from .common import SDKBaseModel


class ReviewPage(SDKBaseModel):
    """Resolved review target page."""

    page_number: int
    page_hash: str
    project_id: str


class ReviewProgressCounts(SDKBaseModel):
    """Progress counters for scout or specialist work."""

    pending: int = 0
    in_progress: int = 0
    completed: int = 0
    failed: int = 0
    total: int = 0


class ReviewSpecialistProgress(ReviewProgressCounts):
    """Specialist-specific progress counters."""

    out_of_scope: int = 0
    max_turns: Optional[int] = None
    active: List["ReviewActiveSpecialist"] = Field(default_factory=list)


class ReviewActiveSpecialist(SDKBaseModel):
    """Live detail for one in-progress specialist."""

    question_id: str
    agent: str
    turns_used: Optional[int] = None
    max_turns: Optional[int] = None
    updated_at: Optional[datetime] = None


class ReviewProgress(SDKBaseModel):
    """Combined review progress payload."""

    scout: Optional[ReviewProgressCounts] = None
    specialist: Optional[ReviewSpecialistProgress] = None


class Review(SDKBaseModel):
    """Unified review model across create, list, and get endpoints."""

    review_id: str
    status: Optional[str] = None
    total_pages: Optional[int] = None
    pages: List[ReviewPage] = Field(default_factory=list)
    owner_user_id: Optional[str] = None
    file_hash: Optional[str] = None
    page_selector: Optional[str] = None
    requested_project_ids: Optional[List[str]] = None
    custom_instructions: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: Optional[ReviewProgress] = None

    @property
    def is_running(self) -> bool:
        return self.status == "running"

    @property
    def is_complete(self) -> bool:
        return self.status == "completed"

    @property
    def is_partial(self) -> bool:
        return self.status == "completed_partial"

    @property
    def is_failed(self) -> bool:
        return self.status == "failed"

    @property
    def is_terminal(self) -> bool:
        return self.status in {"completed", "completed_partial", "failed"}


class ReviewListResponse(SDKBaseModel):
    """Response for GET /v1/reviews."""

    reviews: List[Review] = Field(default_factory=list)


class ReviewQuestion(SDKBaseModel):
    """Persisted review question."""

    question_id: str
    review_id: str
    review_page_id: Optional[str] = None
    source: str
    status: str
    page_hash: str
    project_id: str
    question: str
    location_description: Optional[str] = None
    assigned_agents: List[str] = Field(default_factory=list)
    spawned_by_question_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    turns_used: Optional[int] = None
    error: Optional[str] = None
    raw_model_output: Any = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ReviewQuestionsResult(SDKBaseModel):
    """Response for GET /v1/reviews/{review_id}/questions."""

    review_id: str
    questions: List[ReviewQuestion] = Field(default_factory=list)


class ReviewIssue(SDKBaseModel):
    """Persisted review issue."""

    issue_id: str
    review_id: str
    question_id: str
    project_id: str
    page_hash: str
    agent: str
    priority: str
    category: Optional[str] = None
    title: str
    description: str
    evidence: List[str] = Field(default_factory=list)
    suggested_fix: Optional[str] = None
    created_at: Optional[datetime] = None


class ReviewIssuesResult(SDKBaseModel):
    """Response for GET /v1/reviews/{review_id}/issues."""

    review_id: str
    issues: List[ReviewIssue] = Field(default_factory=list)


class ReviewLogFile(SDKBaseModel):
    """One JSONL log file returned by GET /v1/reviews/{review_id}/logs."""

    name: str
    size_bytes: int
    line_count: int
    entries: List[Any] = Field(default_factory=list)


class ReviewLogsResult(SDKBaseModel):
    """Response for GET /v1/reviews/{review_id}/logs."""

    review_id: str
    files: List[ReviewLogFile] = Field(default_factory=list)


class ReviewArtifactResult(SDKBaseModel):
    """Local file result returned by review artifact download helpers."""

    ok: bool = True
    output_path: str
    bytes_written: int
    content_type: str
