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
Command line entry point of the Antares Web MCP server.

Usage::

    antares-web-mcp --url http://localhost:8080

Every option can also be set through an environment variable, which is the usual way
MCP clients (Claude Code, VS Code / GitHub Copilot, ...) configure a server.

Important: with the ``stdio`` transport, stdout carries the MCP protocol messages.
Nothing else must be written to stdout (logs go to stderr).
"""

import logging
import sys

import click

from antares_web_mcp.client import AntaresWebClient
from antares_web_mcp.server import create_server

DEFAULT_URL = "http://localhost:8080"


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--url",
    envvar="ANTARES_WEB_URL",
    default=DEFAULT_URL,
    show_default=True,
    help="Root URL of the Antares Web server [env: ANTARES_WEB_URL].",
)
@click.option(
    "--token",
    envvar="ANTARES_WEB_TOKEN",
    default=None,
    help="Bearer token (bot token recommended), not needed if security is disabled [env: ANTARES_WEB_TOKEN].",
)
@click.option(
    "--read-only",
    envvar="ANTARES_MCP_READ_ONLY",
    is_flag=True,
    default=False,
    help="Only expose tools that do not modify studies [env: ANTARES_MCP_READ_ONLY].",
)
@click.option(
    "--allow-study-deletion",
    envvar="ANTARES_MCP_ALLOW_STUDY_DELETION",
    is_flag=True,
    default=False,
    help="Expose the `delete_study` tool [env: ANTARES_MCP_ALLOW_STUDY_DELETION].",
)
@click.option(
    "--verify-ssl/--no-verify-ssl",
    envvar="ANTARES_WEB_VERIFY_SSL",
    default=True,
    show_default=True,
    help="Verify the TLS certificate of Antares Web [env: ANTARES_WEB_VERIFY_SSL].",
)
@click.option(
    "--timeout",
    envvar="ANTARES_WEB_TIMEOUT",
    type=float,
    default=60.0,
    show_default=True,
    help="HTTP timeout in seconds [env: ANTARES_WEB_TIMEOUT].",
)
@click.option(
    "--transport",
    type=click.Choice(["stdio", "streamable-http"]),
    envvar="ANTARES_MCP_TRANSPORT",
    default="stdio",
    show_default=True,
    help="'stdio' (launched by the MCP client) or 'streamable-http' (shared HTTP server).",
)
@click.option("--host", default="127.0.0.1", show_default=True, help="Bind address for 'streamable-http'.")
@click.option("--port", type=int, default=8765, show_default=True, help="Port for 'streamable-http'.")
def main(
    url: str,
    token: str | None,
    read_only: bool,
    allow_study_deletion: bool,
    verify_ssl: bool,
    timeout: float,
    transport: str,
    host: str,
    port: int,
) -> None:
    """Start the Antares Web MCP server."""
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # one line per request is too verbose

    client = AntaresWebClient(url, token=token, timeout=timeout, verify_ssl=verify_ssl)
    server = create_server(client, read_only=read_only, allow_study_deletion=allow_study_deletion)
    logging.getLogger(__name__).info(f"Antares Web MCP server targeting {url} (transport={transport})")

    if transport == "streamable-http":
        server.run("streamable-http", host=host, port=port)
    else:
        server.run("stdio")


if __name__ == "__main__":
    main()
