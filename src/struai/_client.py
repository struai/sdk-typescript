"""Main StruAI client classes."""

import os
from functools import cached_property
from typing import Optional

from ._base import DEFAULT_BASE_URL, DEFAULT_TIMEOUT, AsyncBaseClient, BaseClient
from ._exceptions import StruAIError
from .resources.drawings import AsyncDrawings, Drawings
from .resources.projects import AsyncProjects, Projects
from .resources.reviews import AsyncReviews, Reviews


class StruAI(BaseClient):
    """StruAI client for drawing analysis API.

    Args:
        api_key: Your API key. Falls back to STRUAI_API_KEY env var.
        base_url: API base URL. Defaults to https://api.stru.ai.
            If no path is provided, /v1 is appended automatically.
        timeout: Request timeout in seconds. Default 60.
        max_retries: Max retry attempts for failed requests. Default 2.

    Example:
        >>> import os
        >>> client = StruAI(api_key=os.environ["STRUAI_API_KEY"])
        >>>
        >>> # Tier 1: Raw detection
        >>> result = client.drawings.analyze("structural.pdf", page=4)
        >>> print(result.annotations.leaders[0].texts_inside[0].text)
        'W12x26'
        >>>
        >>> # Tier 2: Graph + Search
        >>> project = client.projects.create("Building A")
        >>> job = project.sheets.add("structural.pdf", page=4)
        >>> job.wait()
        >>> hits = project.docquery.search("W12x26 beam connections", limit=5)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 2,
    ):
        if api_key is None:
            api_key = os.environ.get("STRUAI_API_KEY")
        if api_key is None:
            raise StruAIError(
                "API key required. Pass api_key or set STRUAI_API_KEY environment variable."
            )

        super().__init__(
            api_key=api_key,
            base_url=base_url or DEFAULT_BASE_URL,
            timeout=timeout,
            max_retries=max_retries,
        )

    @cached_property
    def drawings(self) -> Drawings:
        """Tier 1: Raw detection API."""
        return Drawings(self)

    @cached_property
    def projects(self) -> Projects:
        """Tier 2: project ingest and DocQuery traversal API."""
        return Projects(self)

    @cached_property
    def reviews(self) -> Reviews:
        """Tier 3: async review orchestration API."""
        return Reviews(self)


class AsyncStruAI(AsyncBaseClient):
    """Async StruAI client for drawing analysis API.

    Example:
        >>> import os
        >>> async with AsyncStruAI(api_key=os.environ["STRUAI_API_KEY"]) as client:
        ...     result = await client.drawings.analyze("structural.pdf", page=4)
        ...
        ...     project = await client.projects.create("Building A")
        ...     job = await project.sheets.add("structural.pdf", page=4)
        ...     await job.wait()
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 2,
    ):
        if api_key is None:
            api_key = os.environ.get("STRUAI_API_KEY")
        if api_key is None:
            raise StruAIError(
                "API key required. Pass api_key or set STRUAI_API_KEY environment variable."
            )

        super().__init__(
            api_key=api_key,
            base_url=base_url or DEFAULT_BASE_URL,
            timeout=timeout,
            max_retries=max_retries,
        )

    @cached_property
    def drawings(self) -> AsyncDrawings:
        """Tier 1: Raw detection API."""
        return AsyncDrawings(self)

    @cached_property
    def projects(self) -> AsyncProjects:
        """Tier 2: project ingest and DocQuery traversal API."""
        return AsyncProjects(self)

    @cached_property
    def reviews(self) -> AsyncReviews:
        """Tier 3: async review orchestration API."""
        return AsyncReviews(self)
