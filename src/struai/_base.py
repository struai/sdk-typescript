"""Base HTTP client with retry logic."""

import time
from typing import Any, Dict, Optional, Type, TypeVar, Union
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel

from ._exceptions import (
    APIError,
    AuthenticationError,
    ConnectionError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)
from ._version import __version__

T = TypeVar("T", bound=BaseModel)
RequestResult = Union[T, Dict[str, Any], bytes, None]

DEFAULT_BASE_URL = "https://api.stru.ai"
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 2


def _normalize_base_url(base_url: str) -> str:
    trimmed = base_url.rstrip("/")
    parsed = urlparse(trimmed)
    if parsed.scheme and parsed.netloc:
        path = parsed.path.rstrip("/")
        if path in ("", "/"):
            return f"{trimmed}/v1"
        return trimmed
    if trimmed.endswith("/v1"):
        return trimmed
    return f"{trimmed}/v1"


class BaseClient:
    """Base HTTP client with retry logic."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        self.api_key = api_key
        self.base_url = _normalize_base_url(base_url)
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                headers=self._default_headers(),
                timeout=self.timeout,
            )
        return self._client

    def _default_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": f"struai-python/{__version__}",
            "Accept": "application/json",
        }

    def _handle_response_error(self, response: httpx.Response) -> None:
        """Raise appropriate exception for error responses."""
        if response.status_code < 400:
            return

        try:
            body = response.json()
            error = body.get("error", {})
            message = error.get("message", response.text)
            code = error.get("code")
        except Exception:
            message = response.text
            code = None

        request_id = response.headers.get("x-request-id")

        exc_map = {
            401: AuthenticationError,
            403: PermissionDeniedError,
            404: NotFoundError,
            422: ValidationError,
            429: RateLimitError,
        }

        if response.status_code in exc_map:
            exc_class = exc_map[response.status_code]
        elif response.status_code >= 500:
            exc_class = InternalServerError
        else:
            exc_class = APIError

        if exc_class == RateLimitError:
            retry_after = int(response.headers.get("Retry-After", 30))
            raise RateLimitError(
                message,
                status_code=response.status_code,
                code=code,
                request_id=request_id,
                response=response,
                retry_after=retry_after,
            )

        raise exc_class(
            message,
            status_code=response.status_code,
            code=code,
            request_id=request_id,
            response=response,
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        data: Any = None,
        files: Any = None,
        params: Optional[Dict[str, Any]] = None,
        cast_to: Optional[Type[T]] = None,
        expect_bytes: bool = False,
    ) -> RequestResult:
        """Make HTTP request with retry logic."""
        client = self._get_client()
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                if files or data is not None:
                    response = client.request(method, path, data=data, files=files, params=params)
                else:
                    response = client.request(method, path, json=json, params=params)

                self._handle_response_error(response)

                # Handle empty responses (DELETE)
                if response.status_code == 204 or not response.content:
                    if expect_bytes:
                        return b""
                    return None

                if expect_bytes:
                    return response.content

                result = response.json()
                if cast_to is not None:
                    return cast_to.model_validate(result)
                return result

            except httpx.TimeoutException as e:
                last_error = TimeoutError(f"Request timed out: {e}")
            except httpx.ConnectError as e:
                last_error = ConnectionError(f"Connection failed: {e}")
            except (RateLimitError, InternalServerError) as e:
                last_error = e
                if attempt < self.max_retries:
                    wait = getattr(e, "retry_after", 2 ** (attempt + 1))
                    time.sleep(min(wait, 30))
                    continue
                raise
            except APIError:
                raise

            if attempt < self.max_retries:
                time.sleep(2**attempt)
            else:
                raise last_error

        raise last_error  # type: ignore

    def get(self, path: str, **kwargs) -> Any:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> Any:
        return self._request("POST", path, **kwargs)

    def delete(self, path: str, **kwargs) -> Any:
        return self._request("DELETE", path, **kwargs)

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class AsyncBaseClient:
    """Async base HTTP client with retry logic."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        self.api_key = api_key
        self.base_url = _normalize_base_url(base_url)
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._default_headers(),
                timeout=self.timeout,
            )
        return self._client

    def _default_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": f"struai-python/{__version__}",
            "Accept": "application/json",
        }

    def _handle_response_error(self, response: httpx.Response) -> None:
        """Raise appropriate exception for error responses."""
        if response.status_code < 400:
            return

        try:
            body = response.json()
            error = body.get("error", {})
            message = error.get("message", response.text)
            code = error.get("code")
        except Exception:
            message = response.text
            code = None

        request_id = response.headers.get("x-request-id")

        exc_map = {
            401: AuthenticationError,
            403: PermissionDeniedError,
            404: NotFoundError,
            422: ValidationError,
            429: RateLimitError,
        }

        if response.status_code in exc_map:
            exc_class = exc_map[response.status_code]
        elif response.status_code >= 500:
            exc_class = InternalServerError
        else:
            exc_class = APIError

        if exc_class == RateLimitError:
            retry_after = int(response.headers.get("Retry-After", 30))
            raise RateLimitError(
                message,
                status_code=response.status_code,
                code=code,
                request_id=request_id,
                response=response,
                retry_after=retry_after,
            )

        raise exc_class(
            message,
            status_code=response.status_code,
            code=code,
            request_id=request_id,
            response=response,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        data: Any = None,
        files: Any = None,
        params: Optional[Dict[str, Any]] = None,
        cast_to: Optional[Type[T]] = None,
        expect_bytes: bool = False,
    ) -> RequestResult:
        """Make async HTTP request with retry logic."""
        import asyncio

        client = await self._get_client()
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                if files or data is not None:
                    response = await client.request(
                        method, path, data=data, files=files, params=params
                    )
                else:
                    response = await client.request(method, path, json=json, params=params)

                self._handle_response_error(response)

                if response.status_code == 204 or not response.content:
                    if expect_bytes:
                        return b""
                    return None

                if expect_bytes:
                    return response.content

                result = response.json()
                if cast_to is not None:
                    return cast_to.model_validate(result)
                return result

            except httpx.TimeoutException as e:
                last_error = TimeoutError(f"Request timed out: {e}")
            except httpx.ConnectError as e:
                last_error = ConnectionError(f"Connection failed: {e}")
            except (RateLimitError, InternalServerError) as e:
                last_error = e
                if attempt < self.max_retries:
                    wait = getattr(e, "retry_after", 2 ** (attempt + 1))
                    await asyncio.sleep(min(wait, 30))
                    continue
                raise
            except APIError:
                raise

            if attempt < self.max_retries:
                await asyncio.sleep(2**attempt)
            else:
                raise last_error

        raise last_error  # type: ignore

    async def get(self, path: str, **kwargs) -> Any:
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> Any:
        return await self._request("POST", path, **kwargs)

    async def delete(self, path: str, **kwargs) -> Any:
        return await self._request("DELETE", path, **kwargs)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
