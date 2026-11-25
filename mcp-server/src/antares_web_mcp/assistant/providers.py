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
Registry of model providers.

To add one: implement `ChatProvider` in its own module, and add a builder to `PROVIDERS`.
Credentials are read from environment variables, set by the Antares Web backend from its
configuration: they never transit through command-line arguments or request bodies.
"""

import os
from collections.abc import Callable

import httpx2

from antares_web_mcp.assistant.openai_provider import OpenAICompatibleProvider
from antares_web_mcp.assistant.provider import ChatProvider, ProviderError

API_KEY_ENV = "OPENAI_API_KEY"


def _build_openai(model: str | None, base_url: str | None, reasoning_effort: str | None) -> ChatProvider:
    # No default endpoint: the content of the studies must not go to a server nobody chose.
    if not base_url:
        raise ProviderError("No model endpoint: set `assistant.base_url` in the Antares Web configuration file.")
    if not model:
        raise ProviderError(
            f"No model: set `assistant.model` in the Antares Web configuration file "
            f"(`GET {base_url.rstrip('/')}/models` lists the models of the endpoint)."
        )
    api_key = os.environ.get(API_KEY_ENV)  # not needed by a server on the local machine
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    return OpenAICompatibleProvider(
        httpx2.AsyncClient(base_url=base_url.rstrip("/") + "/", headers=headers),
        model=model,
        reasoning_effort=reasoning_effort,
    )


PROVIDERS: dict[str, Callable[[str | None, str | None, str | None], ChatProvider]] = {"openai": _build_openai}


def build_provider(
    name: str, *, model: str | None, base_url: str | None, reasoning_effort: str | None = None
) -> ChatProvider:
    """
    Builds the provider `name` for the model `model` served at `base_url`.

    `reasoning_effort`: how much the model reasons before it answers, for the servers which let a request
    choose (not sent by default).

    Raises:
        ProviderError: if the provider is unknown or not configured.
    """
    builder = PROVIDERS.get(name)
    if builder is None:
        raise ProviderError(f"Unknown provider '{name}'. Available providers: {sorted(PROVIDERS)}.")
    return builder(model, base_url, reasoning_effort)
