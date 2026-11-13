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
`antares-web-assistant`: the process started by the Antares Web backend for each chat request.

Protocol: one `AssistantRequest` as JSON on stdin; events on stdout, one JSON object per line
(`tool_call`, `tool_result`, `text`), ending with a `done` event (answer, history, usage) or an
`error` event. Logs go to stderr. The model API key comes from the environment.

Running the agent in its own process keeps its dependencies (model SDK, MCP SDK) out of the
backend environment, and a crashed or stuck turn can be killed without impact on the server.
"""

import asyncio
import json
import logging
import sys
from typing import Any, TextIO

import click
from pydantic import ValidationError

from antares_web_mcp.assistant.agent import AssistantRequest, run_assistant
from antares_web_mcp.assistant.provider import ProviderError
from antares_web_mcp.assistant.providers import build_provider

logger = logging.getLogger(__name__)


async def handle(raw_request: str, out: TextIO) -> None:
    """Runs one turn and writes its events to `out`. Never raises: failures become an `error` event."""

    async def emit(event: dict[str, Any]) -> None:
        out.write(json.dumps(event, ensure_ascii=False) + "\n")
        out.flush()  # the backend forwards events as they come

    try:
        request = AssistantRequest.model_validate_json(raw_request)
        provider = build_provider(request.provider, model=request.model, effort=request.effort)
        result = await run_assistant(request, provider, emit)
    except ValidationError as e:
        await emit({"type": "error", "message": f"Invalid assistant request: {e}"})
    except ProviderError as e:
        await emit({"type": "error", "message": str(e)})
    except Exception as e:
        logger.exception("Assistant turn failed")
        await emit({"type": "error", "message": f"The assistant failed unexpectedly: {e}"})
    else:
        await emit({"type": "done", "provider": provider.name, **result.model_dump()})


@click.command()
def main() -> None:
    """Answer one assistant request read from stdin (started by the Antares Web backend)."""
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    asyncio.run(handle(sys.stdin.read(), sys.stdout))


if __name__ == "__main__":
    main()
