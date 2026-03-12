"""StruAI exceptions."""

from typing import Optional

import httpx


class StruAIError(Exception):
    """Base exception for all StruAI errors."""

    pass


class APIError(StruAIError):
    """API returned an error response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        code: Optional[str] = None,
        request_id: Optional[str] = None,
        response: Optional[httpx.Response] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.request_id = request_id
        self.response = response

    def __str__(self) -> str:
        parts = [self.message]
        if self.code:
            parts.append(f"code={self.code}")
        if self.status_code:
            parts.append(f"status={self.status_code}")
        return " ".join(parts)


class AuthenticationError(APIError):
    """Invalid or missing API key (401)."""

    pass


class PermissionDeniedError(APIError):
    """Insufficient permissions (403)."""

    pass


class NotFoundError(APIError):
    """Resource not found (404)."""

    pass


class ValidationError(APIError):
    """Invalid request parameters (422)."""

    pass


class RateLimitError(APIError):
    """Rate limit exceeded (429)."""

    def __init__(
        self,
        message: str,
        *,
        retry_after: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class InternalServerError(APIError):
    """Server error (5xx)."""

    pass


class TimeoutError(StruAIError):
    """Request timed out."""

    pass


class ConnectionError(StruAIError):
    """Network connection failed."""

    pass


class JobFailedError(StruAIError):
    """Async job failed."""

    def __init__(self, message: str, *, job_id: str, error: str):
        super().__init__(message)
        self.job_id = job_id
        self.error = error


class ReviewFailedError(StruAIError):
    """Async review failed."""

    def __init__(self, message: str, *, review_id: str):
        super().__init__(message)
        self.review_id = review_id
