# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

"""
Thin asynchronous client for the Antares Web REST API.

The MCP server is a *client* of the public REST API and must not import backend internals:
this keeps it deployable next to any Antares Web instance (desktop, local, production).
It uses ``httpx2``, the successor of ``httpx``, which ``mcp`` already depends on.

Methods map 1:1 to REST endpoints and return the decoded JSON. Business logic (combining
several calls, choosing defaults, compacting outputs) belongs to the MCP tools.
"""

import asyncio
import contextlib
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx2

# Status codes of Antares Web background tasks (``antarest.core.tasks.model.TaskStatus``).
TASK_COMPLETED = 3
TASK_FINAL_STATUSES = {3, 4, 5, 6}  # completed, failed, timeout, cancelled


class AntaresWebError(Exception):
    """An error reported by Antares Web (or the inability to reach it), with a model-readable message."""


class AntaresWebClient:
    """
    Asynchronous client for the subset of the Antares Web REST API exposed through MCP.

    Args:
        base_url: Root URL of the Antares Web server (e.g. ``http://localhost:8080``).
        token: Optional bearer token (a bot token created in Antares Web is recommended).
        timeout: Timeout in seconds for each HTTP request.
        verify_ssl: Whether to verify the server TLS certificate.
        transport: Custom transport, mainly used to inject a mock in tests.
    """

    def __init__(
        self,
        base_url: str,
        *,
        token: str | None = None,
        timeout: float = 30.0,
        verify_ssl: bool = True,
        transport: httpx2.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._http = httpx2.AsyncClient(
            base_url=f"{self.base_url}/v1",
            headers=headers,
            timeout=timeout,
            verify=verify_ssl,
            transport=transport,
        )
        # Assistants often send several tool calls at once, but Antares Web rewrites the INI files of a study
        # in place: concurrent writes on the same study can fail ("Could not match section antares").
        # Modifying requests are therefore sent one at a time; reads stay concurrent.
        self._write_lock = asyncio.Lock()

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _send(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        files: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> httpx2.Response:
        lock: contextlib.AbstractAsyncContextManager[Any] = (
            contextlib.nullcontext() if method == "GET" else self._write_lock
        )
        try:
            async with lock:
                response = await self._http.request(
                    method,
                    path,
                    params=params,
                    json=json,
                    files=files,
                    timeout=timeout if timeout is not None else self.timeout,
                )
        except httpx2.TimeoutException as e:
            raise AntaresWebError(f"Antares Web at {self.base_url} did not answer in time ({method} {path}).") from e
        except httpx2.TransportError as e:
            raise AntaresWebError(f"Cannot reach Antares Web at {self.base_url}: {e}") from e

        if response.is_error:
            raise AntaresWebError(_format_error(response))
        return response

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        files: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> Any:
        response = await self._send(method, path, params=params, json=json, files=files, timeout=timeout)
        if not response.content:
            return None
        return response.json()

    # ----------------------------------------------------------------------
    # Studies
    # ----------------------------------------------------------------------

    async def list_studies(
        self,
        *,
        name: str = "",
        versions: list[str] | None = None,
        tags: list[str] | None = None,
        variant: bool | None = None,
        archived: bool | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"name": name, "sortBy": "+name", "pageNb": 0, "pageSize": limit}
        if versions:
            params["versions"] = ",".join(versions)
        if tags:
            params["tags"] = ",".join(tags)
        if variant is not None:
            params["variant"] = variant
        if archived is not None:
            params["archived"] = archived
        studies: dict[str, dict[str, Any]] = await self._request("GET", "/studies", params=params)
        return list(studies.values())

    async def get_study(self, study_id: str) -> dict[str, Any]:
        result: dict[str, Any] = await self._request("GET", f"/studies/{_seg(study_id)}")
        return result

    async def get_study_synthesis(self, study_id: str) -> dict[str, Any]:
        result: dict[str, Any] = await self._request("GET", f"/studies/{_seg(study_id)}/synthesis")
        return result

    async def list_study_versions(self) -> list[str]:
        result: list[str] = await self._request("GET", "/studies/_versions")
        return result

    async def create_study(self, name: str, *, version: str | None = None, directory: str | None = None) -> str:
        params: dict[str, Any] = {"name": name}
        if version:
            params["version"] = version
        if directory:
            params["directory"] = directory
        study_id: str = await self._request("POST", "/studies", params=params)
        return study_id

    async def copy_study(self, study_id: str, new_name: str, *, with_outputs: bool = False) -> str:
        """Starts the copy and returns the id of the background task."""
        params = {"study_name": new_name, "with_outputs": with_outputs, "use_task": True}
        task_id: str = await self._request("POST", f"/studies/{_seg(study_id)}/copy", params=params)
        return task_id

    async def import_study(self, archive: Path, *, groups: list[str] | None = None, timeout: float) -> str:
        """Uploads a study archive (``.zip`` or ``.7z``) and returns the id of the imported study."""
        content_type = "application/x-7z-compressed" if archive.suffix.lower() == ".7z" else "application/zip"
        params = {"groups": ",".join(groups)} if groups else None
        with archive.open("rb") as stream:
            study_id: str = await self._request(
                "POST",
                "/studies/_import",
                params=params,
                files={"study": (archive.name, stream, content_type)},
                timeout=timeout,
            )
        return study_id

    async def create_variant(self, study_id: str, name: str) -> str:
        variant_id: str = await self._request("POST", f"/studies/{_seg(study_id)}/variants", params={"name": name})
        return variant_id

    async def delete_study(self, study_id: str, *, children: bool = False) -> None:
        await self._request("DELETE", f"/studies/{_seg(study_id)}", params={"children": children})

    async def get_general_config(self, study_id: str) -> dict[str, Any]:
        result: dict[str, Any] = await self._request("GET", f"/studies/{_seg(study_id)}/config/general/form")
        return result

    async def update_general_config(self, study_id: str, changes: dict[str, Any]) -> None:
        await self._request("PUT", f"/studies/{_seg(study_id)}/config/general/form", json=changes)

    async def get_config_form(self, study_id: str, form: str) -> dict[str, Any]:
        """``form``: ``general``, ``optimization``, ``advancedparameters``, ``adequacypatch``, ``playlist``..."""
        result: dict[str, Any] = await self._request("GET", f"/studies/{_seg(study_id)}/config/{_seg(form)}/form")
        return result

    async def get_scenario_builder(self, study_id: str) -> dict[str, Any]:
        """Rules of the active ruleset, by symbol (``l`` load, ``t`` thermal, ``h`` hydro, ``bc``...)."""
        result: dict[str, Any] = await self._request("GET", f"/studies/{_seg(study_id)}/config/scenariobuilder")
        return result

    async def get_comments(self, study_id: str) -> str:
        result: str | None = await self._request("GET", f"/studies/{_seg(study_id)}/comments")
        return result or ""

    async def get_parents(self, study_id: str) -> list[dict[str, Any]]:
        """Ancestors of a variant, from its direct parent to the root study (empty for a raw study)."""
        result: list[dict[str, Any]] = await self._request("GET", f"/studies/{_seg(study_id)}/parents")
        return result

    async def list_commands(self, study_id: str) -> list[dict[str, Any]]:
        """Commands of a variant: its changes compared to its parent. Not available for raw studies."""
        result: list[dict[str, Any]] = await self._request("GET", f"/studies/{_seg(study_id)}/commands")
        return result

    async def list_districts(self, study_id: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = await self._request("GET", f"/studies/{_seg(study_id)}/districts")
        return result

    async def get_table(self, study_id: str, table_type: str, columns: list[str] | None = None) -> dict[str, Any]:
        """
        Properties of all the objects of a type in one call (the "table mode" of the UI).
        ``table_type``: ``areas``, ``links``, ``thermals``, ``renewables``, ``st-storages``,
        ``binding-constraints``. Rows are keyed by ``area``, ``area1 / area2`` or ``area / cluster``.
        """
        params = {"columns": ",".join(columns)} if columns else None
        result: dict[str, Any] = await self._request(
            "GET", f"/studies/{_seg(study_id)}/table-mode/{_seg(table_type)}", params=params
        )
        return result

    async def list_binding_constraints(self, study_id: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = await self._request("GET", f"/studies/{_seg(study_id)}/bindingconstraints")
        return result

    async def get_hydro_form(self, study_id: str, area_id: str) -> dict[str, Any]:
        result: dict[str, Any] = await self._request(
            "GET", f"/studies/{_seg(study_id)}/areas/{_seg(area_id)}/hydro/form"
        )
        return result

    async def get_raw(self, study_id: str, path: str, *, depth: int = 1) -> Any:
        """Content of a node of the study tree: a folder listing, INI content or a JSON matrix."""
        return await self._request(
            "GET", f"/studies/{_seg(study_id)}/raw", params={"path": path, "depth": depth, "formatted": True}
        )

    async def get_raw_text(self, study_id: str, path: str) -> str:
        """Content of a text file of the study (e.g. a log in ``logs/`` or a file in ``user/``)."""
        response = await self._send("GET", f"/studies/{_seg(study_id)}/raw", params={"path": path, "formatted": False})
        content_type = response.headers.get("content-type", "")
        if not content_type.startswith(("text/", "application/json")):
            raise AntaresWebError(f"'{path}' is not a text file (content type: {content_type or 'unknown'}).")
        return response.text

    async def get_matrix(self, study_id: str, path: str) -> list[list[float]]:
        """Values of a matrix of the study (rows of columns), e.g. ``input/load/series/load_fr``."""
        matrix: dict[str, Any] = await self.get_raw(study_id, path)
        if not isinstance(matrix, dict) or "data" not in matrix:
            raise AntaresWebError(f"'{path}' is not a matrix.")
        data: list[list[float]] = matrix["data"]
        return data

    async def get_matrix_by_id(self, matrix_id: str) -> list[list[float]]:
        """Values of a matrix of the matrix store, e.g. a matrix referenced by a variant command."""
        matrix: dict[str, Any] = await self._request("GET", f"/matrix/{_seg(matrix_id)}")
        data: list[list[float]] = matrix.get("data") or []
        return data

    # ----------------------------------------------------------------------
    # Background tasks and downloads
    # ----------------------------------------------------------------------

    async def wait_for_task(self, task_id: str, *, timeout: int) -> dict[str, Any]:
        """Waits (server side) for the completion of a background task, at most ``timeout`` seconds."""
        result: dict[str, Any] = await self._request(
            "GET",
            f"/tasks/{_seg(task_id)}",
            params={"wait_for_completion": True, "timeout": timeout},
            timeout=timeout + 30,
        )
        return result

    async def download_text(self, download_id: str, *, timeout: int = 300) -> str:
        """Waits for a file prepared in the background by Antares Web, then returns its content."""
        metadata: dict[str, Any] = await self._request(
            "GET",
            f"/downloads/{_seg(download_id)}/metadata",
            params={"wait_for_availability": True},
            timeout=timeout,
        )
        if metadata.get("failed"):
            raise AntaresWebError(f"Antares Web failed to prepare the file: {metadata.get('error_message')}")
        response = await self._send("GET", f"/downloads/{_seg(download_id)}", timeout=timeout)
        return response.text

    # ----------------------------------------------------------------------
    # Areas
    # ----------------------------------------------------------------------

    async def list_areas(self, study_id: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = await self._request("GET", f"/studies/{_seg(study_id)}/areas")
        return result

    async def create_area(self, study_id: str, name: str) -> dict[str, Any]:
        result: dict[str, Any] = await self._request("POST", f"/studies/{_seg(study_id)}/areas", json={"name": name})
        return result

    async def delete_area(self, study_id: str, area_id: str) -> str:
        result: str = await self._request("DELETE", f"/studies/{_seg(study_id)}/areas/{_seg(area_id)}")
        return result

    async def get_area_properties(self, study_id: str, area_id: str) -> dict[str, Any]:
        result: dict[str, Any] = await self._request(
            "GET", f"/studies/{_seg(study_id)}/areas/{_seg(area_id)}/properties/form"
        )
        return result

    async def update_area_properties(self, study_id: str, area_id: str, changes: dict[str, Any]) -> None:
        await self._request("PUT", f"/studies/{_seg(study_id)}/areas/{_seg(area_id)}/properties/form", json=changes)

    # ----------------------------------------------------------------------
    # Links
    # ----------------------------------------------------------------------

    async def list_links(self, study_id: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = await self._request("GET", f"/studies/{_seg(study_id)}/links")
        return result

    async def create_link(self, study_id: str, link: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = await self._request("POST", f"/studies/{_seg(study_id)}/links", json=link)
        return result

    async def update_link(self, study_id: str, area1: str, area2: str, changes: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = await self._request(
            "PUT", f"/studies/{_seg(study_id)}/links/{_seg(area1)}/{_seg(area2)}", json=changes
        )
        return result

    async def delete_link(self, study_id: str, area1: str, area2: str) -> str:
        result: str = await self._request("DELETE", f"/studies/{_seg(study_id)}/links/{_seg(area1)}/{_seg(area2)}")
        return result

    # ----------------------------------------------------------------------
    # Clusters (thermal, renewable) and short-term storages
    # ----------------------------------------------------------------------

    async def list_clusters(self, study_id: str, area_id: str, kind: str) -> list[dict[str, Any]]:
        """``kind`` is the URL segment: ``clusters/thermal``, ``clusters/renewable`` or ``storages``."""
        result: list[dict[str, Any]] = await self._request(
            "GET", f"/studies/{_seg(study_id)}/areas/{_seg(area_id)}/{kind}"
        )
        return result

    async def create_cluster(self, study_id: str, area_id: str, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = await self._request(
            "POST", f"/studies/{_seg(study_id)}/areas/{_seg(area_id)}/{kind}", json=payload
        )
        return result

    async def update_cluster(
        self, study_id: str, area_id: str, kind: str, cluster_id: str, changes: dict[str, Any]
    ) -> dict[str, Any]:
        result: dict[str, Any] = await self._request(
            "PATCH", f"/studies/{_seg(study_id)}/areas/{_seg(area_id)}/{kind}/{_seg(cluster_id)}", json=changes
        )
        return result

    async def delete_clusters(self, study_id: str, area_id: str, kind: str, cluster_ids: list[str]) -> None:
        await self._request("DELETE", f"/studies/{_seg(study_id)}/areas/{_seg(area_id)}/{kind}", json=cluster_ids)

    # ----------------------------------------------------------------------
    # Matrices (time series)
    # ----------------------------------------------------------------------

    async def edit_matrix(self, study_id: str, path: str, operation: str, value: float) -> None:
        """
        Applies ``<cell> <operation> value`` (operation in ``=``, ``+``, ``-``, ``*``, ``/``) to every
        cell of an hourly matrix (8760 rows), whatever its number of columns (time series).
        """
        instructions = [
            {
                # Bounds are inclusive; the column range is clamped to the actual matrix width.
                "slices": [{"row_from": 0, "row_to": 8759, "column_from": 0, "column_to": 9999}],
                "operation": {"operation": operation, "value": value},
            }
        ]
        await self._request("PUT", f"/studies/{_seg(study_id)}/matrix", params={"path": path}, json=instructions)

    # ----------------------------------------------------------------------
    # Launcher
    # ----------------------------------------------------------------------

    async def list_launchers(self) -> dict[str, Any]:
        result: dict[str, Any] = await self._request("GET", "/launcher/launchers")
        return result

    async def launch_study(
        self,
        study_id: str,
        *,
        launcher: str | None = None,
        solver_version: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> str:
        params: dict[str, Any] = {}
        if launcher:
            params["launcher"] = launcher
        if solver_version:
            params["version"] = solver_version
        result: dict[str, Any] = await self._request(
            "POST", f"/launcher/run/{_seg(study_id)}", params=params, json=parameters or {}
        )
        job_id: str = result["job_id"]
        return job_id

    async def get_job(self, job_id: str) -> dict[str, Any]:
        result: dict[str, Any] = await self._request("GET", f"/launcher/jobs/{_seg(job_id)}")
        return result

    async def get_job_progress(self, job_id: str) -> float | None:
        result: float | None = await self._request("GET", f"/launcher/jobs/{_seg(job_id)}/progress")
        return result

    async def list_jobs(self, *, study_id: str | None = None, latest: int | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if study_id:
            params["study"] = study_id
        if latest:
            params["latest"] = latest
        result: list[dict[str, Any]] = await self._request("GET", "/launcher/jobs", params=params)
        return result

    async def get_job_logs(self, job_id: str, *, log_type: str) -> str:
        result: str | None = await self._request(
            "GET", f"/launcher/jobs/{_seg(job_id)}/logs", params={"log_type": log_type}
        )
        return result or ""

    async def kill_job(self, job_id: str) -> None:
        await self._request("POST", f"/launcher/jobs/{_seg(job_id)}/kill")

    # ----------------------------------------------------------------------
    # Outputs
    # ----------------------------------------------------------------------

    async def list_outputs(self, study_id: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = await self._request("GET", f"/studies/{_seg(study_id)}/outputs")
        return result

    async def aggregate_output(
        self,
        study_id: str,
        output_id: str,
        *,
        target: str,
        query_file: str,
        frequency: str,
        ids: list[str] | None = None,
    ) -> str:
        """
        Starts the aggregation of the Monte-Carlo synthesis (``mc-all``) of an output for areas or links
        (``target``) and returns the CSV content.
        """
        params: dict[str, Any] = {"query_file": query_file, "frequency": frequency, "format": "csv"}
        if ids:
            params[f"{target}_ids"] = ",".join(ids)
        download_id: str = await self._request(
            "GET",
            f"/studies/{_seg(study_id)}/outputs/{_seg(output_id)}/aggregate/{target}/mc-all",
            params=params,
        )
        return await self.download_text(download_id)


def _seg(value: str) -> str:
    """Encode a value as a single URL path segment (prevents path traversal through tool arguments)."""
    return quote(value, safe="")


def _format_error(response: httpx2.Response) -> str:
    """
    Builds a concise message from an Antares Web error response.

    Antares Web errors look like ``{"description": "...", "exception": "StudyNotFoundError"}``,
    while FastAPI validation errors look like ``{"detail": [...]}``.
    """
    prefix = f"Antares Web returned HTTP {response.status_code}"
    try:
        body = response.json()
    except ValueError:
        text = response.text.strip()
        return f"{prefix}: {text[:500]}" if text else prefix

    if isinstance(body, dict):
        exception = body.get("exception")
        description = body.get("description")
        detail = body.get("detail")
        if description or exception:
            return f"{prefix} ({exception or 'error'}): {description}"
        if detail:
            return f"{prefix}: {detail}"
    return f"{prefix}: {body}"
