"""Tier 2 projects, ingest jobs, and DocQuery traversal resources."""

from __future__ import annotations

import asyncio
import time
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from .._exceptions import JobFailedError, TimeoutError
from ..models.docquery import (
    DocQueryCropResult,
    DocQueryCypherResult,
    DocQueryNeighborsResult,
    DocQueryNodeGetResult,
    DocQueryReferenceResolveResult,
    DocQuerySearchResult,
    DocQuerySheetEntitiesResult,
    DocQuerySheetListResult,
    DocQuerySheetSummaryResult,
)
from ..models.projects import (
    JobStatus,
    Project,
    ProjectDeleteResult,
    SheetDeleteResult,
    SheetIngestResponse,
    SheetResult,
)
from ._uploads import Uploadable, _prepare_file
from .drawings import _compute_file_hash

if TYPE_CHECKING:
    from .._base import AsyncBaseClient, BaseClient


# =============================================================================
# Job handles
# =============================================================================


class Job:
    """Handle for one async sheet-ingestion job (sync)."""

    def __init__(
        self,
        client: "BaseClient",
        project_id: str,
        job_id: str,
        page: Optional[int] = None,
    ):
        self._client = client
        self._project_id = project_id
        self._job_id = job_id
        self._page = page

    @property
    def id(self) -> str:
        return self._job_id

    @property
    def page(self) -> Optional[int]:
        return self._page

    def status(self) -> JobStatus:
        """Fetch current job status."""
        return self._client.get(
            f"/projects/{self._project_id}/jobs/{self._job_id}",
            cast_to=JobStatus,
        )

    def wait(self, timeout: float = 120, poll_interval: float = 2) -> SheetResult:
        """Wait for completion and return resulting sheet info."""
        start = time.time()
        while time.time() - start < timeout:
            status = self.status()
            if status.is_complete:
                if status.result is None:
                    return SheetResult()
                return status.result
            if status.is_failed:
                raise JobFailedError(
                    f"Job {self._job_id} failed: {status.error}",
                    job_id=self._job_id,
                    error=status.error or "Unknown error",
                )
            time.sleep(poll_interval)

        raise TimeoutError(f"Job {self._job_id} did not complete within {timeout}s")


class AsyncJob:
    """Handle for one async sheet-ingestion job (async)."""

    def __init__(
        self,
        client: "AsyncBaseClient",
        project_id: str,
        job_id: str,
        page: Optional[int] = None,
    ):
        self._client = client
        self._project_id = project_id
        self._job_id = job_id
        self._page = page

    @property
    def id(self) -> str:
        return self._job_id

    @property
    def page(self) -> Optional[int]:
        return self._page

    async def status(self) -> JobStatus:
        """Fetch current job status."""
        return await self._client.get(
            f"/projects/{self._project_id}/jobs/{self._job_id}",
            cast_to=JobStatus,
        )

    async def wait(self, timeout: float = 120, poll_interval: float = 2) -> SheetResult:
        """Wait for completion and return resulting sheet info."""
        start = time.time()
        while time.time() - start < timeout:
            status = await self.status()
            if status.is_complete:
                if status.result is None:
                    return SheetResult()
                return status.result
            if status.is_failed:
                raise JobFailedError(
                    f"Job {self._job_id} failed: {status.error}",
                    job_id=self._job_id,
                    error=status.error or "Unknown error",
                )
            await asyncio.sleep(poll_interval)

        raise TimeoutError(f"Job {self._job_id} did not complete within {timeout}s")


class JobBatch:
    """Batch of jobs returned by a multi-page sheet ingest request (sync)."""

    def __init__(self, jobs: List[Job]):
        self.jobs = jobs

    @property
    def ids(self) -> List[str]:
        return [job.id for job in self.jobs]

    def status_all(self) -> List[JobStatus]:
        return [job.status() for job in self.jobs]

    def wait_all(
        self,
        timeout_per_job: float = 120,
        poll_interval: float = 2,
    ) -> List[SheetResult]:
        return [job.wait(timeout=timeout_per_job, poll_interval=poll_interval) for job in self.jobs]


class AsyncJobBatch:
    """Batch of jobs returned by a multi-page sheet ingest request (async)."""

    def __init__(self, jobs: List[AsyncJob]):
        self.jobs = jobs

    @property
    def ids(self) -> List[str]:
        return [job.id for job in self.jobs]

    async def status_all(self) -> List[JobStatus]:
        return list(await asyncio.gather(*(job.status() for job in self.jobs)))

    async def wait_all(
        self,
        timeout_per_job: float = 120,
        poll_interval: float = 2,
    ) -> List[SheetResult]:
        return list(
            await asyncio.gather(
                *(
                    job.wait(timeout=timeout_per_job, poll_interval=poll_interval)
                    for job in self.jobs
                )
            )
        )


# =============================================================================
# Helpers
# =============================================================================


def _normalize_page_selector(page: Union[int, str]) -> str:
    if isinstance(page, int):
        return str(page)
    text = str(page).strip()
    if not text:
        raise ValueError("page is required")
    return text


def _jobs_from_response(
    client: "BaseClient",
    project_id: str,
    payload: SheetIngestResponse,
) -> List[Job]:
    jobs: List[Job] = []
    for item in payload.jobs:
        jobs.append(Job(client, project_id, item.job_id, page=item.page))
    return jobs


def _async_jobs_from_response(
    client: "AsyncBaseClient", project_id: str, payload: SheetIngestResponse
) -> List[AsyncJob]:
    jobs: List[AsyncJob] = []
    for item in payload.jobs:
        jobs.append(AsyncJob(client, project_id, item.job_id, page=item.page))
    return jobs


def _normalize_text(value: Any, *, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required")
    return text


def _records(payload: DocQueryCypherResult) -> List[Dict[str, Any]]:
    return [row for row in payload.records if isinstance(row, dict)]


def _parse_bbox_value(
    bbox: Union[str, List[Any], Tuple[Any, Any, Any, Any]],
) -> Tuple[float, float, float, float]:
    if isinstance(bbox, str):
        text = bbox.strip()
        if not text:
            raise ValueError("bbox is required")
        parts = text.replace(",", " ").split()
    elif isinstance(bbox, (list, tuple)):
        parts = [str(item) for item in bbox]
    else:
        raise ValueError("bbox must be a string or a list/tuple of four numbers")

    if len(parts) != 4:
        raise ValueError("bbox must contain four values: x1,y1,x2,y2")
    try:
        x1, y1, x2, y2 = [float(value) for value in parts]
    except ValueError as exc:
        raise ValueError("bbox values must be numeric") from exc
    return x1, y1, x2, y2


# =============================================================================
# Sheets
# =============================================================================


class Sheets:
    """Sheet ingestion and deletion API (sync)."""

    def __init__(self, client: "BaseClient", project_id: str):
        self._client = client
        self._project_id = project_id

    def add(
        self,
        file: Optional[Uploadable] = None,
        *,
        page: Union[int, str] = 1,
        file_hash: Optional[str] = None,
        source_description: Optional[str] = None,
        on_sheet_exists: Optional[str] = None,
        community_update_mode: Optional[str] = None,
        semantic_index_update_mode: Optional[str] = None,
    ) -> Union[Job, JobBatch]:
        """Queue sheet ingestion jobs."""
        if file is None and not file_hash:
            raise ValueError("Provide file or file_hash")
        if file is not None and file_hash:
            raise ValueError("Provide either file or file_hash, not both")

        if file is not None and file_hash is None:
            computed_hash = _compute_file_hash(file)
            cache = self._client.get(f"/drawings/cache/{computed_hash}")
            if cache.get("cached"):
                file = None
                file_hash = computed_hash

        selector = _normalize_page_selector(page)
        data: Dict[str, str] = {"page": selector}
        if file_hash:
            data["file_hash"] = file_hash
        if source_description is not None:
            data["source_description"] = source_description
        if on_sheet_exists:
            data["on_sheet_exists"] = on_sheet_exists
        if community_update_mode:
            data["community_update_mode"] = community_update_mode
        if semantic_index_update_mode:
            data["semantic_index_update_mode"] = semantic_index_update_mode

        upload = None
        handle = None
        try:
            if file is not None:
                upload, handle = _prepare_file(file)

            response = self._client.post(
                f"/projects/{self._project_id}/sheets",
                files=upload,
                data=data,
                cast_to=SheetIngestResponse,
            )
        finally:
            if handle is not None:
                handle.close()

        jobs = _jobs_from_response(self._client, self._project_id, response)
        if len(jobs) == 1:
            return jobs[0]
        return JobBatch(jobs)

    def delete(self, sheet_id: str) -> SheetDeleteResult:
        """Delete a sheet and return cleanup stats."""
        return self._client.delete(
            f"/projects/{self._project_id}/sheets/{sheet_id}",
            cast_to=SheetDeleteResult,
        )

    def job(self, job_id: str, *, page: Optional[int] = None) -> Job:
        """Construct a job handle for a known job id."""
        return Job(self._client, self._project_id, job_id, page=page)


class AsyncSheets:
    """Sheet ingestion and deletion API (async)."""

    def __init__(self, client: "AsyncBaseClient", project_id: str):
        self._client = client
        self._project_id = project_id

    async def add(
        self,
        file: Optional[Uploadable] = None,
        *,
        page: Union[int, str] = 1,
        file_hash: Optional[str] = None,
        source_description: Optional[str] = None,
        on_sheet_exists: Optional[str] = None,
        community_update_mode: Optional[str] = None,
        semantic_index_update_mode: Optional[str] = None,
    ) -> Union[AsyncJob, AsyncJobBatch]:
        """Queue sheet ingestion jobs."""
        if file is None and not file_hash:
            raise ValueError("Provide file or file_hash")
        if file is not None and file_hash:
            raise ValueError("Provide either file or file_hash, not both")

        if file is not None and file_hash is None:
            computed_hash = _compute_file_hash(file)
            cache = await self._client.get(f"/drawings/cache/{computed_hash}")
            if cache.get("cached"):
                file = None
                file_hash = computed_hash

        selector = _normalize_page_selector(page)
        data: Dict[str, str] = {"page": selector}
        if file_hash:
            data["file_hash"] = file_hash
        if source_description is not None:
            data["source_description"] = source_description
        if on_sheet_exists:
            data["on_sheet_exists"] = on_sheet_exists
        if community_update_mode:
            data["community_update_mode"] = community_update_mode
        if semantic_index_update_mode:
            data["semantic_index_update_mode"] = semantic_index_update_mode

        upload = None
        handle = None
        try:
            if file is not None:
                upload, handle = _prepare_file(file)
            response = await self._client.post(
                f"/projects/{self._project_id}/sheets",
                files=upload,
                data=data,
                cast_to=SheetIngestResponse,
            )
        finally:
            if handle is not None:
                handle.close()

        jobs = _async_jobs_from_response(self._client, self._project_id, response)
        if len(jobs) == 1:
            return jobs[0]
        return AsyncJobBatch(jobs)

    async def delete(self, sheet_id: str) -> SheetDeleteResult:
        """Delete a sheet and return cleanup stats."""
        return await self._client.delete(
            f"/projects/{self._project_id}/sheets/{sheet_id}",
            cast_to=SheetDeleteResult,
        )

    def job(self, job_id: str, *, page: Optional[int] = None) -> AsyncJob:
        """Construct a job handle for a known job id."""
        return AsyncJob(self._client, self._project_id, job_id, page=page)


# =============================================================================
# DocQuery traversal
# =============================================================================


class DocQuery:
    """DocQuery traversal API (sync)."""

    def __init__(self, client: "BaseClient", project_id: str):
        self._client = client
        self._project_id = project_id

    def node_get(self, uuid: str) -> DocQueryNodeGetResult:
        uuid = _normalize_text(uuid, field_name="uuid")
        return self._client.get(
            f"/projects/{self._project_id}/node-get",
            params={"uuid": uuid},
            cast_to=DocQueryNodeGetResult,
        )

    def sheet_entities(
        self,
        sheet_id: str,
        *,
        entity_type: Optional[str] = None,
        limit: int = 200,
    ) -> DocQuerySheetEntitiesResult:
        sheet_id = _normalize_text(sheet_id, field_name="sheet_id")
        params: Dict[str, Any] = {"sheet_id": sheet_id, "limit": int(limit)}
        if entity_type is not None:
            params["entity_type"] = str(entity_type)
        return self._client.get(
            f"/projects/{self._project_id}/sheet-entities",
            params=params,
            cast_to=DocQuerySheetEntitiesResult,
        )

    def search(
        self,
        query: str,
        *,
        index: str = "entity_search",
        limit: int = 20,
    ) -> DocQuerySearchResult:
        query = _normalize_text(query, field_name="query")
        index = _normalize_text(index, field_name="index")
        return self._client.get(
            f"/projects/{self._project_id}/search",
            params={"query": query, "index": index, "limit": int(limit)},
            cast_to=DocQuerySearchResult,
        )

    def neighbors(
        self,
        uuid: str,
        *,
        mode: str = "both",
        direction: str = "both",
        relationship_type: Optional[str] = None,
        radius: float = 200.0,
        limit: int = 50,
    ) -> DocQueryNeighborsResult:
        uuid = _normalize_text(uuid, field_name="uuid")
        mode = _normalize_text(mode, field_name="mode").lower()
        if mode not in {"graph", "spatial", "both"}:
            raise ValueError("mode must be one of: graph, spatial, both")
        direction = _normalize_text(direction, field_name="direction").lower()
        if direction not in {"in", "out", "both"}:
            raise ValueError("direction must be one of: in, out, both")
        params: Dict[str, Any] = {
            "uuid": uuid,
            "mode": mode,
            "direction": direction,
            "radius": float(radius),
            "limit": int(limit),
        }
        if relationship_type is not None:
            params["relationship_type"] = str(relationship_type)
        return self._client.get(
            f"/projects/{self._project_id}/neighbors",
            params=params,
            cast_to=DocQueryNeighborsResult,
        )

    def cypher(
        self,
        query: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        max_rows: int = 500,
    ) -> DocQueryCypherResult:
        query = _normalize_text(query, field_name="query")
        body: Dict[str, Any] = {
            "query": query,
            "params": dict(params or {}),
            "max_rows": int(max_rows),
        }
        return self._client.post(
            f"/projects/{self._project_id}/cypher",
            json=body,
            cast_to=DocQueryCypherResult,
        )

    def sheet_summary(self, sheet_id: str, *, orphan_limit: int = 10) -> DocQuerySheetSummaryResult:
        sheet_id = _normalize_text(sheet_id, field_name="sheet_id")
        safe_orphan_limit = max(1, min(int(orphan_limit), 200))

        sheet_node_payload = self.cypher(
            "MATCH (s:Entity:Sheet {project_id:$project_id, sheet_id:$sheet_id}) "
            "RETURN s.sheet_id AS sheet_id, s.uuid AS uuid, "
            "coalesce(s.name, s.text) AS name LIMIT 1",
            params={"sheet_id": sheet_id},
            max_rows=1,
        )
        label_counts_payload = self.cypher(
            "MATCH (n:Entity {project_id:$project_id, sheet_id:$sheet_id}) "
            "UNWIND labels(n) AS label "
            "WITH label WHERE label <> 'Entity' "
            "RETURN label, count(*) AS count ORDER BY count DESC, label",
            params={"sheet_id": sheet_id},
            max_rows=500,
        )
        rel_counts_payload = self.cypher(
            "MATCH ()-[r]->() "
            "WHERE r.project_id = $project_id "
            "  AND $sheet_id IN coalesce(r.source_sheet_ids, []) "
            "RETURN type(r) AS rel_type, count(*) AS count "
            "ORDER BY count DESC, rel_type",
            params={"sheet_id": sheet_id},
            max_rows=500,
        )
        reachability_payload = self.cypher(
            "OPTIONAL MATCH (s:Entity:Sheet {project_id:$project_id, sheet_id:$sheet_id}) "
            "MATCH (n:Entity {project_id:$project_id, sheet_id:$sheet_id}) "
            "WITH s, collect(n) AS nodes "
            "UNWIND nodes AS n "
            "WITH s, n, n:Sheet AS is_sheet "
            "RETURN "
            "(s IS NOT NULL) AS has_sheet_node, "
            "count(CASE WHEN is_sheet THEN 1 END) AS sheet_node_count, "
            "count(CASE WHEN NOT is_sheet THEN 1 END) AS non_sheet_total, "
            "count(CASE WHEN NOT is_sheet AND s IS NOT NULL "
            "           AND EXISTS { MATCH (s)<-[:LOCATED_IN*1..2]-(n) } "
            "      THEN 1 END) AS reachable_non_sheet",
            params={"sheet_id": sheet_id},
            max_rows=1,
        )
        orphan_payload = self.cypher(
            "MATCH (n:Entity {project_id:$project_id, sheet_id:$sheet_id}) "
            "WHERE NOT n:Sheet "
            "  AND NOT EXISTS { "
            "    MATCH (s:Entity:Sheet {project_id:$project_id, sheet_id:$sheet_id})"
            "<-[:LOCATED_IN*1..2]-(n) "
            "  } "
            "RETURN n.uuid AS uuid, "
            "       [l IN labels(n) WHERE l <> 'Entity'] AS labels, "
            "       n.category AS category, "
            "       coalesce(n.name, n.text) AS name "
            "ORDER BY coalesce(n.name, n.text), n.uuid "
            "LIMIT $orphan_limit",
            params={"sheet_id": sheet_id, "orphan_limit": safe_orphan_limit},
            max_rows=safe_orphan_limit,
        )

        sheet_rows = _records(sheet_node_payload)
        label_rows = _records(label_counts_payload)
        rel_rows = _records(rel_counts_payload)
        reachability_rows = _records(reachability_payload)
        orphan_rows = _records(orphan_payload)

        reachability: Dict[str, Any] = {
            "has_sheet_node": False,
            "sheet_node_count": 0,
            "non_sheet_total": 0,
            "reachable_non_sheet": 0,
            "unreachable_non_sheet": 0,
        }
        if reachability_rows:
            first = reachability_rows[0]
            has_sheet_node = bool(first.get("has_sheet_node"))
            sheet_node_count = int(first.get("sheet_node_count") or 0)
            non_sheet_total = int(first.get("non_sheet_total") or 0)
            reachable_non_sheet = int(first.get("reachable_non_sheet") or 0)
            reachability = {
                "has_sheet_node": has_sheet_node,
                "sheet_node_count": sheet_node_count,
                "non_sheet_total": non_sheet_total,
                "reachable_non_sheet": reachable_non_sheet,
                "unreachable_non_sheet": max(0, non_sheet_total - reachable_non_sheet),
            }

        warnings: List[Dict[str, Any]] = []
        if not reachability["has_sheet_node"]:
            warnings.append(
                {
                    "type": "missing_sheet_node",
                    "message": f"No :Entity:Sheet node found for sheet_id={sheet_id}.",
                }
            )
        if reachability["sheet_node_count"] > 1:
            warnings.append(
                {
                    "type": "duplicate_sheet_nodes",
                    "message": (
                        f"Found {reachability['sheet_node_count']} Sheet nodes for "
                        f"sheet_id={sheet_id}; expected 1."
                    ),
                }
            )
        if reachability["unreachable_non_sheet"] > 0:
            warnings.append(
                {
                    "type": "unreachable_entities",
                    "message": (
                        f"{reachability['unreachable_non_sheet']} non-sheet entities "
                        "are not reachable "
                        f"from sheet {sheet_id} via LOCATED_IN*1..2."
                    ),
                }
            )

        return DocQuerySheetSummaryResult.model_validate(
            {
                "ok": True,
                "command": "sheet-summary",
                "input": {
                    "project_id": self._project_id,
                    "sheet_id": sheet_id,
                    "orphan_limit": safe_orphan_limit,
                },
                "sheet_node": (sheet_rows[0] if sheet_rows else None),
                "node_label_counts": label_rows,
                "relationship_counts": rel_rows,
                "reachability": reachability,
                "orphan_examples": orphan_rows,
                "warnings": warnings,
            }
        )

    def sheet_list(self) -> DocQuerySheetListResult:
        sheet_nodes_payload = self.cypher(
            "MATCH (s:Entity:Sheet {project_id:$project_id}) "
            "RETURN s.sheet_id AS sheet_id, s.uuid AS uuid, coalesce(s.name, s.text) AS name "
            "ORDER BY s.sheet_id, s.uuid",
            max_rows=5000,
        )
        inventory_payload = self.cypher(
            "MATCH (n:Entity {project_id:$project_id}) "
            "RETURN n.sheet_id AS sheet_id, count(n) AS entity_count "
            "ORDER BY n.sheet_id",
            max_rows=5000,
        )
        duplicate_sheet_nodes_payload = self.cypher(
            "MATCH (s:Entity:Sheet {project_id:$project_id}) "
            "WITH s.sheet_id AS sheet_id, count(*) AS sheet_node_count "
            "WHERE sheet_node_count > 1 "
            "RETURN sheet_id, sheet_node_count "
            "ORDER BY sheet_node_count DESC, sheet_id",
            max_rows=200,
        )
        missing_sheet_id_payload = self.cypher(
            "MATCH (n:Entity {project_id:$project_id}) "
            "WHERE n.sheet_id IS NULL OR trim(toString(n.sheet_id)) = '' "
            "RETURN count(n) AS missing_sheet_id_count",
            max_rows=1,
        )

        sheet_nodes = _records(sheet_nodes_payload)
        inventory = _records(inventory_payload)
        duplicate_sheet_nodes = _records(duplicate_sheet_nodes_payload)
        missing_sheet_rows = _records(missing_sheet_id_payload)
        missing_sheet_id_count = (
            int(missing_sheet_rows[0].get("missing_sheet_id_count") or 0)
            if missing_sheet_rows
            else 0
        )

        sheet_node_ids = {str(r["sheet_id"]) for r in sheet_nodes if r.get("sheet_id")}
        inventory_ids = {str(r["sheet_id"]) for r in inventory if r.get("sheet_id")}
        inventory_counts: Dict[str, int] = {
            str(r["sheet_id"]): int(r.get("entity_count") or 0)
            for r in inventory
            if r.get("sheet_id")
        }
        total_entities = sum(int(r.get("entity_count") or 0) for r in inventory)
        inventory_without_sheet_node = sorted(inventory_ids - sheet_node_ids)
        sheet_nodes_without_inventory = sorted(sheet_node_ids - inventory_ids)
        sheet_nodes_with_only_self = sorted(
            sid for sid in sheet_node_ids if inventory_counts.get(sid, 0) == 1
        )

        mismatch_warnings: List[Dict[str, Any]] = []
        if inventory_without_sheet_node:
            mismatch_warnings.append(
                {
                    "type": "inventory_sheet_id_without_sheet_node",
                    "sheet_ids": inventory_without_sheet_node,
                    "message": "Entities exist for sheet_id values that do not have a Sheet node.",
                }
            )
        if sheet_nodes_without_inventory:
            mismatch_warnings.append(
                {
                    "type": "sheet_node_without_inventory",
                    "sheet_ids": sheet_nodes_without_inventory,
                    "message": "Sheet nodes exist with no matching entity inventory rows.",
                }
            )
        if duplicate_sheet_nodes:
            mismatch_warnings.append(
                {
                    "type": "duplicate_sheet_nodes",
                    "duplicates": duplicate_sheet_nodes,
                    "message": "Multiple Sheet nodes found for one or more sheet_id values.",
                }
            )
        if missing_sheet_id_count > 0:
            mismatch_warnings.append(
                {
                    "type": "entities_missing_sheet_id",
                    "count": missing_sheet_id_count,
                    "message": "Some entities are missing sheet_id.",
                }
            )
        if sheet_nodes_with_only_self:
            mismatch_warnings.append(
                {
                    "type": "sheet_nodes_without_non_sheet_entities",
                    "sheet_ids": sheet_nodes_with_only_self,
                    "message": "Sheet IDs where inventory count is only the Sheet node itself.",
                }
            )

        return DocQuerySheetListResult.model_validate(
            {
                "ok": True,
                "command": "sheet-list",
                "input": {
                    "project_id": self._project_id,
                },
                "sheet_nodes": sheet_nodes,
                "entity_sheet_inventory": inventory,
                "totals": {
                    "sheet_node_count": len(sheet_nodes),
                    "inventory_sheet_id_count": len(inventory_ids),
                    "total_entities": total_entities,
                    "missing_sheet_id_count": missing_sheet_id_count,
                },
                "mismatch_warnings": mismatch_warnings,
            }
        )

    def reference_resolve(self, uuid: str, *, limit: int = 100) -> DocQueryReferenceResolveResult:
        node_uuid = _normalize_text(uuid, field_name="uuid")
        safe_limit = max(1, min(int(limit), 200))

        source_payload = self.cypher(
            "MATCH (src:Entity {project_id:$project_id, uuid:$uuid}) "
            "RETURN src.uuid AS uuid, "
            "       [l IN labels(src) WHERE l <> 'Entity'] AS labels, "
            "       src.sheet_id AS sheet_id, "
            "       src.detail_id AS detail_id, "
            "       src.section_id AS section_id, "
            "       src.target_sheets AS target_sheets, "
            "       src.category AS category, "
            "       coalesce(src.name, src.text) AS name, "
            "       src.text AS text "
            "LIMIT 1",
            params={"uuid": node_uuid},
            max_rows=1,
        )
        source_rows = _records(source_payload)
        if not source_rows:
            return DocQueryReferenceResolveResult.model_validate(
                {
                    "ok": True,
                    "command": "reference-resolve",
                    "input": {
                        "project_id": self._project_id,
                        "uuid": node_uuid,
                        "limit": safe_limit,
                    },
                    "found": False,
                    "source": None,
                    "resolved_references": [],
                    "warnings": [
                        {"type": "source_not_found", "message": "No source node found for uuid."}
                    ],
                }
            )

        source = source_rows[0]
        source_labels = source.get("labels") if isinstance(source.get("labels"), list) else []
        source_target_sheets = (
            source.get("target_sheets") if isinstance(source.get("target_sheets"), list) else []
        )

        references_payload = self.cypher(
            "MATCH (src:Entity {project_id:$project_id, uuid:$uuid}) "
            "OPTIONAL MATCH (src)-[r:REFERENCES]->(t:Entity {project_id:$project_id}) "
            "OPTIONAL MATCH (t)-[:LOCATED_IN]->(loc1:Entity {project_id:$project_id}) "
            "OPTIONAL MATCH (loc1)-[:LOCATED_IN]->(loc2:Entity {project_id:$project_id}) "
            "RETURN r.rel_uuid AS rel_uuid, "
            "       r.fact AS fact, "
            "       r.source_sheet_ids AS source_sheet_ids, "
            "       r.meta_target_sheet AS meta_target_sheet, "
            "       r.meta_target_detail_id AS meta_target_detail_id, "
            "       r.meta_target_section_id AS meta_target_section_id, "
            "       r.meta_target_kind AS meta_target_kind, "
            "       t.uuid AS target_uuid, "
            "       [l IN labels(t) WHERE l <> 'Entity'] AS target_labels, "
            "       t.sheet_id AS target_sheet_id, "
            "       t.detail_id AS target_detail_id, "
            "       t.section_id AS target_section_id, "
            "       t.category AS target_category, "
            "       coalesce(t.name, t.text) AS target_name, "
            "       loc1.uuid AS target_located_in_uuid_1, "
            "       [l IN labels(loc1) WHERE l <> 'Entity'] AS target_located_in_labels_1, "
            "       coalesce(loc1.name, loc1.text) AS target_located_in_name_1, "
            "       loc2.uuid AS target_located_in_uuid_2, "
            "       [l IN labels(loc2) WHERE l <> 'Entity'] AS target_located_in_labels_2, "
            "       coalesce(loc2.name, loc2.text) AS target_located_in_name_2 "
            "ORDER BY coalesce(t.sheet_id, ''), coalesce(t.name, t.text, ''), t.uuid "
            "LIMIT $limit",
            params={"uuid": node_uuid, "limit": safe_limit},
            max_rows=safe_limit,
        )
        reference_rows = _records(references_payload)

        resolved_references: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []
        seen: set[tuple[Any, ...]] = set()

        for row in reference_rows:
            rel_uuid = row.get("rel_uuid")
            target_uuid = row.get("target_uuid")
            if rel_uuid is None and target_uuid is None:
                continue

            key = (
                rel_uuid,
                target_uuid,
                row.get("target_located_in_uuid_1"),
                row.get("target_located_in_uuid_2"),
            )
            if key in seen:
                continue
            seen.add(key)

            target_sheet_id = row.get("target_sheet_id")
            meta_target_sheet = row.get("meta_target_sheet")
            sheet_match_meta = None
            if target_sheet_id is not None and meta_target_sheet is not None:
                sheet_match_meta = str(target_sheet_id) == str(meta_target_sheet)

            sheet_in_source_targets = None
            if target_sheet_id is not None and source_target_sheets:
                sheet_in_source_targets = str(target_sheet_id) in {
                    str(sid) for sid in source_target_sheets
                }

            traversal_path: List[Dict[str, Any]] = [
                {"from_uuid": node_uuid, "rel_type": "REFERENCES", "to_uuid": target_uuid},
            ]
            if row.get("target_located_in_uuid_1"):
                traversal_path.append(
                    {
                        "from_uuid": target_uuid,
                        "rel_type": "LOCATED_IN",
                        "to_uuid": row.get("target_located_in_uuid_1"),
                    }
                )
            if row.get("target_located_in_uuid_2"):
                traversal_path.append(
                    {
                        "from_uuid": row.get("target_located_in_uuid_1"),
                        "rel_type": "LOCATED_IN",
                        "to_uuid": row.get("target_located_in_uuid_2"),
                    }
                )

            resolved_references.append(
                {
                    "relationship": {
                        "rel_uuid": rel_uuid,
                        "fact": row.get("fact"),
                        "source_sheet_ids": row.get("source_sheet_ids"),
                        "meta_target_sheet": meta_target_sheet,
                        "meta_target_detail_id": row.get("meta_target_detail_id"),
                        "meta_target_section_id": row.get("meta_target_section_id"),
                        "meta_target_kind": row.get("meta_target_kind"),
                    },
                    "target": {
                        "uuid": target_uuid,
                        "labels": row.get("target_labels"),
                        "sheet_id": target_sheet_id,
                        "detail_id": row.get("target_detail_id"),
                        "section_id": row.get("target_section_id"),
                        "category": row.get("target_category"),
                        "name": row.get("target_name"),
                    },
                    "target_context": {
                        "located_in_1": {
                            "uuid": row.get("target_located_in_uuid_1"),
                            "labels": row.get("target_located_in_labels_1"),
                            "name": row.get("target_located_in_name_1"),
                        },
                        "located_in_2": {
                            "uuid": row.get("target_located_in_uuid_2"),
                            "labels": row.get("target_located_in_labels_2"),
                            "name": row.get("target_located_in_name_2"),
                        },
                    },
                    "checks": {
                        "target_sheet_matches_meta_target_sheet": sheet_match_meta,
                        "target_sheet_in_source_target_sheets": sheet_in_source_targets,
                    },
                    "traversal_path": traversal_path,
                }
            )

            if sheet_match_meta is False:
                warnings.append(
                    {
                        "type": "meta_target_sheet_mismatch",
                        "rel_uuid": rel_uuid,
                        "message": "Target sheet_id does not match relationship meta_target_sheet.",
                    }
                )
            if sheet_in_source_targets is False:
                warnings.append(
                    {
                        "type": "source_target_sheets_mismatch",
                        "rel_uuid": rel_uuid,
                        "message": "Target sheet_id is not listed in source target_sheets.",
                    }
                )

        if "Callout" not in source_labels:
            warnings.append(
                {
                    "type": "source_not_callout",
                    "message": "Source node is not labeled Callout; references may still exist.",
                }
            )
        if not resolved_references:
            warnings.append(
                {
                    "type": "no_outgoing_references",
                    "message": "No outgoing REFERENCES edges found for this source node.",
                }
            )

        return DocQueryReferenceResolveResult.model_validate(
            {
                "ok": True,
                "command": "reference-resolve",
                "input": {"project_id": self._project_id, "uuid": node_uuid, "limit": safe_limit},
                "found": True,
                "source": source,
                "resolved_references": resolved_references,
                "count": len(resolved_references),
                "warnings": warnings,
            }
        )

    def crop(
        self,
        *,
        output: Union[str, Path],
        uuid: Optional[str] = None,
        bbox: Optional[Union[str, List[Any], Tuple[Any, Any, Any, Any]]] = None,
        page_hash: Optional[str] = None,
    ) -> DocQueryCropResult:
        if bool(uuid) == (bbox is not None):
            raise ValueError("provide exactly one of uuid or bbox")

        output_text = _normalize_text(str(output), field_name="output")
        body: Dict[str, Any] = {}
        if uuid:
            body["uuid"] = _normalize_text(uuid, field_name="uuid")
        else:
            body["bbox"] = list(_parse_bbox_value(bbox if bbox is not None else ""))
            page_hash_value = _normalize_text(page_hash, field_name="page_hash")
            body["page_hash"] = page_hash_value

        png_bytes = self._client.post(
            f"/projects/{self._project_id}/crop",
            json=body,
            expect_bytes=True,
        )
        if not isinstance(png_bytes, bytes):
            raise ValueError("crop endpoint did not return image bytes")

        content_type = "image/png"
        output_path = Path(output_text).expanduser()
        if not output_path.is_absolute():
            output_path = Path.cwd() / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(png_bytes)

        return DocQueryCropResult.model_validate(
            {
                "ok": True,
                "output_path": str(output_path),
                "bytes_written": len(png_bytes),
                "content_type": content_type,
            }
        )


class AsyncDocQuery:
    """DocQuery traversal API (async)."""

    def __init__(self, client: "AsyncBaseClient", project_id: str):
        self._client = client
        self._project_id = project_id

    async def node_get(self, uuid: str) -> DocQueryNodeGetResult:
        uuid = _normalize_text(uuid, field_name="uuid")
        return await self._client.get(
            f"/projects/{self._project_id}/node-get",
            params={"uuid": uuid},
            cast_to=DocQueryNodeGetResult,
        )

    async def sheet_entities(
        self,
        sheet_id: str,
        *,
        entity_type: Optional[str] = None,
        limit: int = 200,
    ) -> DocQuerySheetEntitiesResult:
        sheet_id = _normalize_text(sheet_id, field_name="sheet_id")
        params: Dict[str, Any] = {"sheet_id": sheet_id, "limit": int(limit)}
        if entity_type is not None:
            params["entity_type"] = str(entity_type)
        return await self._client.get(
            f"/projects/{self._project_id}/sheet-entities",
            params=params,
            cast_to=DocQuerySheetEntitiesResult,
        )

    async def search(
        self,
        query: str,
        *,
        index: str = "entity_search",
        limit: int = 20,
    ) -> DocQuerySearchResult:
        query = _normalize_text(query, field_name="query")
        index = _normalize_text(index, field_name="index")
        return await self._client.get(
            f"/projects/{self._project_id}/search",
            params={"query": query, "index": index, "limit": int(limit)},
            cast_to=DocQuerySearchResult,
        )

    async def neighbors(
        self,
        uuid: str,
        *,
        mode: str = "both",
        direction: str = "both",
        relationship_type: Optional[str] = None,
        radius: float = 200.0,
        limit: int = 50,
    ) -> DocQueryNeighborsResult:
        uuid = _normalize_text(uuid, field_name="uuid")
        mode = _normalize_text(mode, field_name="mode").lower()
        if mode not in {"graph", "spatial", "both"}:
            raise ValueError("mode must be one of: graph, spatial, both")
        direction = _normalize_text(direction, field_name="direction").lower()
        if direction not in {"in", "out", "both"}:
            raise ValueError("direction must be one of: in, out, both")
        params: Dict[str, Any] = {
            "uuid": uuid,
            "mode": mode,
            "direction": direction,
            "radius": float(radius),
            "limit": int(limit),
        }
        if relationship_type is not None:
            params["relationship_type"] = str(relationship_type)
        return await self._client.get(
            f"/projects/{self._project_id}/neighbors",
            params=params,
            cast_to=DocQueryNeighborsResult,
        )

    async def cypher(
        self,
        query: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        max_rows: int = 500,
    ) -> DocQueryCypherResult:
        query = _normalize_text(query, field_name="query")
        body: Dict[str, Any] = {
            "query": query,
            "params": dict(params or {}),
            "max_rows": int(max_rows),
        }
        return await self._client.post(
            f"/projects/{self._project_id}/cypher",
            json=body,
            cast_to=DocQueryCypherResult,
        )

    async def sheet_summary(
        self,
        sheet_id: str,
        *,
        orphan_limit: int = 10,
    ) -> DocQuerySheetSummaryResult:
        sheet_id = _normalize_text(sheet_id, field_name="sheet_id")
        safe_orphan_limit = max(1, min(int(orphan_limit), 200))

        sheet_node_payload = await self.cypher(
            "MATCH (s:Entity:Sheet {project_id:$project_id, sheet_id:$sheet_id}) "
            "RETURN s.sheet_id AS sheet_id, s.uuid AS uuid, "
            "coalesce(s.name, s.text) AS name LIMIT 1",
            params={"sheet_id": sheet_id},
            max_rows=1,
        )
        label_counts_payload = await self.cypher(
            "MATCH (n:Entity {project_id:$project_id, sheet_id:$sheet_id}) "
            "UNWIND labels(n) AS label "
            "WITH label WHERE label <> 'Entity' "
            "RETURN label, count(*) AS count ORDER BY count DESC, label",
            params={"sheet_id": sheet_id},
            max_rows=500,
        )
        rel_counts_payload = await self.cypher(
            "MATCH ()-[r]->() "
            "WHERE r.project_id = $project_id "
            "  AND $sheet_id IN coalesce(r.source_sheet_ids, []) "
            "RETURN type(r) AS rel_type, count(*) AS count "
            "ORDER BY count DESC, rel_type",
            params={"sheet_id": sheet_id},
            max_rows=500,
        )
        reachability_payload = await self.cypher(
            "OPTIONAL MATCH (s:Entity:Sheet {project_id:$project_id, sheet_id:$sheet_id}) "
            "MATCH (n:Entity {project_id:$project_id, sheet_id:$sheet_id}) "
            "WITH s, collect(n) AS nodes "
            "UNWIND nodes AS n "
            "WITH s, n, n:Sheet AS is_sheet "
            "RETURN "
            "(s IS NOT NULL) AS has_sheet_node, "
            "count(CASE WHEN is_sheet THEN 1 END) AS sheet_node_count, "
            "count(CASE WHEN NOT is_sheet THEN 1 END) AS non_sheet_total, "
            "count(CASE WHEN NOT is_sheet AND s IS NOT NULL "
            "           AND EXISTS { MATCH (s)<-[:LOCATED_IN*1..2]-(n) } "
            "      THEN 1 END) AS reachable_non_sheet",
            params={"sheet_id": sheet_id},
            max_rows=1,
        )
        orphan_payload = await self.cypher(
            "MATCH (n:Entity {project_id:$project_id, sheet_id:$sheet_id}) "
            "WHERE NOT n:Sheet "
            "  AND NOT EXISTS { "
            "    MATCH (s:Entity:Sheet {project_id:$project_id, sheet_id:$sheet_id})"
            "<-[:LOCATED_IN*1..2]-(n) "
            "  } "
            "RETURN n.uuid AS uuid, "
            "       [l IN labels(n) WHERE l <> 'Entity'] AS labels, "
            "       n.category AS category, "
            "       coalesce(n.name, n.text) AS name "
            "ORDER BY coalesce(n.name, n.text), n.uuid "
            "LIMIT $orphan_limit",
            params={"sheet_id": sheet_id, "orphan_limit": safe_orphan_limit},
            max_rows=safe_orphan_limit,
        )

        sheet_rows = _records(sheet_node_payload)
        label_rows = _records(label_counts_payload)
        rel_rows = _records(rel_counts_payload)
        reachability_rows = _records(reachability_payload)
        orphan_rows = _records(orphan_payload)

        reachability: Dict[str, Any] = {
            "has_sheet_node": False,
            "sheet_node_count": 0,
            "non_sheet_total": 0,
            "reachable_non_sheet": 0,
            "unreachable_non_sheet": 0,
        }
        if reachability_rows:
            first = reachability_rows[0]
            has_sheet_node = bool(first.get("has_sheet_node"))
            sheet_node_count = int(first.get("sheet_node_count") or 0)
            non_sheet_total = int(first.get("non_sheet_total") or 0)
            reachable_non_sheet = int(first.get("reachable_non_sheet") or 0)
            reachability = {
                "has_sheet_node": has_sheet_node,
                "sheet_node_count": sheet_node_count,
                "non_sheet_total": non_sheet_total,
                "reachable_non_sheet": reachable_non_sheet,
                "unreachable_non_sheet": max(0, non_sheet_total - reachable_non_sheet),
            }

        warnings: List[Dict[str, Any]] = []
        if not reachability["has_sheet_node"]:
            warnings.append(
                {
                    "type": "missing_sheet_node",
                    "message": f"No :Entity:Sheet node found for sheet_id={sheet_id}.",
                }
            )
        if reachability["sheet_node_count"] > 1:
            warnings.append(
                {
                    "type": "duplicate_sheet_nodes",
                    "message": (
                        f"Found {reachability['sheet_node_count']} Sheet nodes for "
                        f"sheet_id={sheet_id}; expected 1."
                    ),
                }
            )
        if reachability["unreachable_non_sheet"] > 0:
            warnings.append(
                {
                    "type": "unreachable_entities",
                    "message": (
                        f"{reachability['unreachable_non_sheet']} non-sheet entities "
                        "are not reachable "
                        f"from sheet {sheet_id} via LOCATED_IN*1..2."
                    ),
                }
            )

        return DocQuerySheetSummaryResult.model_validate(
            {
                "ok": True,
                "command": "sheet-summary",
                "input": {
                    "project_id": self._project_id,
                    "sheet_id": sheet_id,
                    "orphan_limit": safe_orphan_limit,
                },
                "sheet_node": (sheet_rows[0] if sheet_rows else None),
                "node_label_counts": label_rows,
                "relationship_counts": rel_rows,
                "reachability": reachability,
                "orphan_examples": orphan_rows,
                "warnings": warnings,
            }
        )

    async def sheet_list(self) -> DocQuerySheetListResult:
        sheet_nodes_payload = await self.cypher(
            "MATCH (s:Entity:Sheet {project_id:$project_id}) "
            "RETURN s.sheet_id AS sheet_id, s.uuid AS uuid, coalesce(s.name, s.text) AS name "
            "ORDER BY s.sheet_id, s.uuid",
            max_rows=5000,
        )
        inventory_payload = await self.cypher(
            "MATCH (n:Entity {project_id:$project_id}) "
            "RETURN n.sheet_id AS sheet_id, count(n) AS entity_count "
            "ORDER BY n.sheet_id",
            max_rows=5000,
        )
        duplicate_sheet_nodes_payload = await self.cypher(
            "MATCH (s:Entity:Sheet {project_id:$project_id}) "
            "WITH s.sheet_id AS sheet_id, count(*) AS sheet_node_count "
            "WHERE sheet_node_count > 1 "
            "RETURN sheet_id, sheet_node_count "
            "ORDER BY sheet_node_count DESC, sheet_id",
            max_rows=200,
        )
        missing_sheet_id_payload = await self.cypher(
            "MATCH (n:Entity {project_id:$project_id}) "
            "WHERE n.sheet_id IS NULL OR trim(toString(n.sheet_id)) = '' "
            "RETURN count(n) AS missing_sheet_id_count",
            max_rows=1,
        )

        sheet_nodes = _records(sheet_nodes_payload)
        inventory = _records(inventory_payload)
        duplicate_sheet_nodes = _records(duplicate_sheet_nodes_payload)
        missing_sheet_rows = _records(missing_sheet_id_payload)
        missing_sheet_id_count = (
            int(missing_sheet_rows[0].get("missing_sheet_id_count") or 0)
            if missing_sheet_rows
            else 0
        )

        sheet_node_ids = {str(r["sheet_id"]) for r in sheet_nodes if r.get("sheet_id")}
        inventory_ids = {str(r["sheet_id"]) for r in inventory if r.get("sheet_id")}
        inventory_counts: Dict[str, int] = {
            str(r["sheet_id"]): int(r.get("entity_count") or 0)
            for r in inventory
            if r.get("sheet_id")
        }
        total_entities = sum(int(r.get("entity_count") or 0) for r in inventory)
        inventory_without_sheet_node = sorted(inventory_ids - sheet_node_ids)
        sheet_nodes_without_inventory = sorted(sheet_node_ids - inventory_ids)
        sheet_nodes_with_only_self = sorted(
            sid for sid in sheet_node_ids if inventory_counts.get(sid, 0) == 1
        )

        mismatch_warnings: List[Dict[str, Any]] = []
        if inventory_without_sheet_node:
            mismatch_warnings.append(
                {
                    "type": "inventory_sheet_id_without_sheet_node",
                    "sheet_ids": inventory_without_sheet_node,
                    "message": "Entities exist for sheet_id values that do not have a Sheet node.",
                }
            )
        if sheet_nodes_without_inventory:
            mismatch_warnings.append(
                {
                    "type": "sheet_node_without_inventory",
                    "sheet_ids": sheet_nodes_without_inventory,
                    "message": "Sheet nodes exist with no matching entity inventory rows.",
                }
            )
        if duplicate_sheet_nodes:
            mismatch_warnings.append(
                {
                    "type": "duplicate_sheet_nodes",
                    "duplicates": duplicate_sheet_nodes,
                    "message": "Multiple Sheet nodes found for one or more sheet_id values.",
                }
            )
        if missing_sheet_id_count > 0:
            mismatch_warnings.append(
                {
                    "type": "entities_missing_sheet_id",
                    "count": missing_sheet_id_count,
                    "message": "Some entities are missing sheet_id.",
                }
            )
        if sheet_nodes_with_only_self:
            mismatch_warnings.append(
                {
                    "type": "sheet_nodes_without_non_sheet_entities",
                    "sheet_ids": sheet_nodes_with_only_self,
                    "message": "Sheet IDs where inventory count is only the Sheet node itself.",
                }
            )

        return DocQuerySheetListResult.model_validate(
            {
                "ok": True,
                "command": "sheet-list",
                "input": {
                    "project_id": self._project_id,
                },
                "sheet_nodes": sheet_nodes,
                "entity_sheet_inventory": inventory,
                "totals": {
                    "sheet_node_count": len(sheet_nodes),
                    "inventory_sheet_id_count": len(inventory_ids),
                    "total_entities": total_entities,
                    "missing_sheet_id_count": missing_sheet_id_count,
                },
                "mismatch_warnings": mismatch_warnings,
            }
        )

    async def reference_resolve(
        self,
        uuid: str,
        *,
        limit: int = 100,
    ) -> DocQueryReferenceResolveResult:
        node_uuid = _normalize_text(uuid, field_name="uuid")
        safe_limit = max(1, min(int(limit), 200))

        source_payload = await self.cypher(
            "MATCH (src:Entity {project_id:$project_id, uuid:$uuid}) "
            "RETURN src.uuid AS uuid, "
            "       [l IN labels(src) WHERE l <> 'Entity'] AS labels, "
            "       src.sheet_id AS sheet_id, "
            "       src.detail_id AS detail_id, "
            "       src.section_id AS section_id, "
            "       src.target_sheets AS target_sheets, "
            "       src.category AS category, "
            "       coalesce(src.name, src.text) AS name, "
            "       src.text AS text "
            "LIMIT 1",
            params={"uuid": node_uuid},
            max_rows=1,
        )
        source_rows = _records(source_payload)
        if not source_rows:
            return DocQueryReferenceResolveResult.model_validate(
                {
                    "ok": True,
                    "command": "reference-resolve",
                    "input": {
                        "project_id": self._project_id,
                        "uuid": node_uuid,
                        "limit": safe_limit,
                    },
                    "found": False,
                    "source": None,
                    "resolved_references": [],
                    "warnings": [
                        {"type": "source_not_found", "message": "No source node found for uuid."}
                    ],
                }
            )

        source = source_rows[0]
        source_labels = source.get("labels") if isinstance(source.get("labels"), list) else []
        source_target_sheets = (
            source.get("target_sheets") if isinstance(source.get("target_sheets"), list) else []
        )

        references_payload = await self.cypher(
            "MATCH (src:Entity {project_id:$project_id, uuid:$uuid}) "
            "OPTIONAL MATCH (src)-[r:REFERENCES]->(t:Entity {project_id:$project_id}) "
            "OPTIONAL MATCH (t)-[:LOCATED_IN]->(loc1:Entity {project_id:$project_id}) "
            "OPTIONAL MATCH (loc1)-[:LOCATED_IN]->(loc2:Entity {project_id:$project_id}) "
            "RETURN r.rel_uuid AS rel_uuid, "
            "       r.fact AS fact, "
            "       r.source_sheet_ids AS source_sheet_ids, "
            "       r.meta_target_sheet AS meta_target_sheet, "
            "       r.meta_target_detail_id AS meta_target_detail_id, "
            "       r.meta_target_section_id AS meta_target_section_id, "
            "       r.meta_target_kind AS meta_target_kind, "
            "       t.uuid AS target_uuid, "
            "       [l IN labels(t) WHERE l <> 'Entity'] AS target_labels, "
            "       t.sheet_id AS target_sheet_id, "
            "       t.detail_id AS target_detail_id, "
            "       t.section_id AS target_section_id, "
            "       t.category AS target_category, "
            "       coalesce(t.name, t.text) AS target_name, "
            "       loc1.uuid AS target_located_in_uuid_1, "
            "       [l IN labels(loc1) WHERE l <> 'Entity'] AS target_located_in_labels_1, "
            "       coalesce(loc1.name, loc1.text) AS target_located_in_name_1, "
            "       loc2.uuid AS target_located_in_uuid_2, "
            "       [l IN labels(loc2) WHERE l <> 'Entity'] AS target_located_in_labels_2, "
            "       coalesce(loc2.name, loc2.text) AS target_located_in_name_2 "
            "ORDER BY coalesce(t.sheet_id, ''), coalesce(t.name, t.text, ''), t.uuid "
            "LIMIT $limit",
            params={"uuid": node_uuid, "limit": safe_limit},
            max_rows=safe_limit,
        )
        reference_rows = _records(references_payload)

        resolved_references: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []
        seen: set[tuple[Any, ...]] = set()

        for row in reference_rows:
            rel_uuid = row.get("rel_uuid")
            target_uuid = row.get("target_uuid")
            if rel_uuid is None and target_uuid is None:
                continue

            key = (
                rel_uuid,
                target_uuid,
                row.get("target_located_in_uuid_1"),
                row.get("target_located_in_uuid_2"),
            )
            if key in seen:
                continue
            seen.add(key)

            target_sheet_id = row.get("target_sheet_id")
            meta_target_sheet = row.get("meta_target_sheet")
            sheet_match_meta = None
            if target_sheet_id is not None and meta_target_sheet is not None:
                sheet_match_meta = str(target_sheet_id) == str(meta_target_sheet)

            sheet_in_source_targets = None
            if target_sheet_id is not None and source_target_sheets:
                sheet_in_source_targets = str(target_sheet_id) in {
                    str(sid) for sid in source_target_sheets
                }

            traversal_path: List[Dict[str, Any]] = [
                {"from_uuid": node_uuid, "rel_type": "REFERENCES", "to_uuid": target_uuid},
            ]
            if row.get("target_located_in_uuid_1"):
                traversal_path.append(
                    {
                        "from_uuid": target_uuid,
                        "rel_type": "LOCATED_IN",
                        "to_uuid": row.get("target_located_in_uuid_1"),
                    }
                )
            if row.get("target_located_in_uuid_2"):
                traversal_path.append(
                    {
                        "from_uuid": row.get("target_located_in_uuid_1"),
                        "rel_type": "LOCATED_IN",
                        "to_uuid": row.get("target_located_in_uuid_2"),
                    }
                )

            resolved_references.append(
                {
                    "relationship": {
                        "rel_uuid": rel_uuid,
                        "fact": row.get("fact"),
                        "source_sheet_ids": row.get("source_sheet_ids"),
                        "meta_target_sheet": meta_target_sheet,
                        "meta_target_detail_id": row.get("meta_target_detail_id"),
                        "meta_target_section_id": row.get("meta_target_section_id"),
                        "meta_target_kind": row.get("meta_target_kind"),
                    },
                    "target": {
                        "uuid": target_uuid,
                        "labels": row.get("target_labels"),
                        "sheet_id": target_sheet_id,
                        "detail_id": row.get("target_detail_id"),
                        "section_id": row.get("target_section_id"),
                        "category": row.get("target_category"),
                        "name": row.get("target_name"),
                    },
                    "target_context": {
                        "located_in_1": {
                            "uuid": row.get("target_located_in_uuid_1"),
                            "labels": row.get("target_located_in_labels_1"),
                            "name": row.get("target_located_in_name_1"),
                        },
                        "located_in_2": {
                            "uuid": row.get("target_located_in_uuid_2"),
                            "labels": row.get("target_located_in_labels_2"),
                            "name": row.get("target_located_in_name_2"),
                        },
                    },
                    "checks": {
                        "target_sheet_matches_meta_target_sheet": sheet_match_meta,
                        "target_sheet_in_source_target_sheets": sheet_in_source_targets,
                    },
                    "traversal_path": traversal_path,
                }
            )

            if sheet_match_meta is False:
                warnings.append(
                    {
                        "type": "meta_target_sheet_mismatch",
                        "rel_uuid": rel_uuid,
                        "message": "Target sheet_id does not match relationship meta_target_sheet.",
                    }
                )
            if sheet_in_source_targets is False:
                warnings.append(
                    {
                        "type": "source_target_sheets_mismatch",
                        "rel_uuid": rel_uuid,
                        "message": "Target sheet_id is not listed in source target_sheets.",
                    }
                )

        if "Callout" not in source_labels:
            warnings.append(
                {
                    "type": "source_not_callout",
                    "message": "Source node is not labeled Callout; references may still exist.",
                }
            )
        if not resolved_references:
            warnings.append(
                {
                    "type": "no_outgoing_references",
                    "message": "No outgoing REFERENCES edges found for this source node.",
                }
            )

        return DocQueryReferenceResolveResult.model_validate(
            {
                "ok": True,
                "command": "reference-resolve",
                "input": {"project_id": self._project_id, "uuid": node_uuid, "limit": safe_limit},
                "found": True,
                "source": source,
                "resolved_references": resolved_references,
                "count": len(resolved_references),
                "warnings": warnings,
            }
        )

    async def crop(
        self,
        *,
        output: Union[str, Path],
        uuid: Optional[str] = None,
        bbox: Optional[Union[str, List[Any], Tuple[Any, Any, Any, Any]]] = None,
        page_hash: Optional[str] = None,
    ) -> DocQueryCropResult:
        if bool(uuid) == (bbox is not None):
            raise ValueError("provide exactly one of uuid or bbox")

        output_text = _normalize_text(str(output), field_name="output")
        body: Dict[str, Any] = {}
        if uuid:
            body["uuid"] = _normalize_text(uuid, field_name="uuid")
        else:
            body["bbox"] = list(_parse_bbox_value(bbox if bbox is not None else ""))
            page_hash_value = _normalize_text(page_hash, field_name="page_hash")
            body["page_hash"] = page_hash_value

        png_bytes = await self._client.post(
            f"/projects/{self._project_id}/crop",
            json=body,
            expect_bytes=True,
        )
        if not isinstance(png_bytes, bytes):
            raise ValueError("crop endpoint did not return image bytes")

        content_type = "image/png"
        output_path = Path(output_text).expanduser()
        if not output_path.is_absolute():
            output_path = Path.cwd() / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(png_bytes)

        return DocQueryCropResult.model_validate(
            {
                "ok": True,
                "output_path": str(output_path),
                "bytes_written": len(png_bytes),
                "content_type": content_type,
            }
        )


# =============================================================================
# Project instance
# =============================================================================


class ProjectInstance:
    """Project handle with nested resources (sync)."""

    def __init__(self, client: "BaseClient", project: Project):
        self._client = client
        self._project = project

    @property
    def id(self) -> str:
        return self._project.id

    @property
    def name(self) -> str:
        return self._project.name

    @property
    def description(self) -> Optional[str]:
        return self._project.description

    @property
    def data(self) -> Project:
        """Raw project model data."""
        return self._project

    @cached_property
    def sheets(self) -> Sheets:
        return Sheets(self._client, self.id)

    @cached_property
    def docquery(self) -> DocQuery:
        return DocQuery(self._client, self.id)

    def delete(self) -> ProjectDeleteResult:
        """Delete this project."""
        return self._client.delete(f"/projects/{self.id}", cast_to=ProjectDeleteResult)


class AsyncProjectInstance:
    """Project handle with nested resources (async)."""

    def __init__(self, client: "AsyncBaseClient", project: Project):
        self._client = client
        self._project = project

    @property
    def id(self) -> str:
        return self._project.id

    @property
    def name(self) -> str:
        return self._project.name

    @property
    def description(self) -> Optional[str]:
        return self._project.description

    @property
    def data(self) -> Project:
        """Raw project model data."""
        return self._project

    @cached_property
    def sheets(self) -> AsyncSheets:
        return AsyncSheets(self._client, self.id)

    @cached_property
    def docquery(self) -> AsyncDocQuery:
        return AsyncDocQuery(self._client, self.id)

    async def delete(self) -> ProjectDeleteResult:
        """Delete this project."""
        return await self._client.delete(f"/projects/{self.id}", cast_to=ProjectDeleteResult)


# =============================================================================
# Projects top-level
# =============================================================================


class Projects:
    """Top-level project API (sync)."""

    def __init__(self, client: "BaseClient"):
        self._client = client

    def create(self, name: str, description: Optional[str] = None) -> ProjectInstance:
        """Create a project."""
        project = self._client.post(
            "/projects",
            json={"name": name, "description": description},
            cast_to=Project,
        )
        return ProjectInstance(self._client, project)

    def list(self) -> List[Project]:
        """List projects available to the API key."""
        response = self._client.get("/projects")
        return [Project.model_validate(item) for item in response.get("projects", [])]

    def open(
        self,
        project_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> ProjectInstance:
        """Create a project handle without performing a lookup call."""
        project_id = _normalize_text(project_id, field_name="project_id")
        project = Project.model_validate(
            {
                "id": project_id,
                "name": name or project_id,
                "description": description,
            }
        )
        return ProjectInstance(self._client, project)

    def delete(self, project_id: str) -> ProjectDeleteResult:
        """Delete one project."""
        return self._client.delete(f"/projects/{project_id}", cast_to=ProjectDeleteResult)


class AsyncProjects:
    """Top-level project API (async)."""

    def __init__(self, client: "AsyncBaseClient"):
        self._client = client

    async def create(self, name: str, description: Optional[str] = None) -> AsyncProjectInstance:
        """Create a project."""
        project = await self._client.post(
            "/projects",
            json={"name": name, "description": description},
            cast_to=Project,
        )
        return AsyncProjectInstance(self._client, project)

    async def list(self) -> List[Project]:
        """List projects available to the API key."""
        response = await self._client.get("/projects")
        return [Project.model_validate(item) for item in response.get("projects", [])]

    def open(
        self,
        project_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> AsyncProjectInstance:
        """Create a project handle without performing a lookup call."""
        project_id = _normalize_text(project_id, field_name="project_id")
        project = Project.model_validate(
            {
                "id": project_id,
                "name": name or project_id,
                "description": description,
            }
        )
        return AsyncProjectInstance(self._client, project)

    async def delete(self, project_id: str) -> ProjectDeleteResult:
        """Delete one project."""
        return await self._client.delete(f"/projects/{project_id}", cast_to=ProjectDeleteResult)


__all__ = [
    "Projects",
    "AsyncProjects",
    "ProjectInstance",
    "AsyncProjectInstance",
    "Sheets",
    "AsyncSheets",
    "DocQuery",
    "AsyncDocQuery",
    "Job",
    "AsyncJob",
    "JobBatch",
    "AsyncJobBatch",
]
