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

To add a vendor: implement `ChatProvider` in its own module, and add a builder to `PROVIDERS`.
Credentials are read from environment variables, set by the Antares Web backend from its
configuration: they never transit through command-line arguments or request bodies.
"""

import os
from collections.abc import Callable

import anthropic

from antares_web_mcp.assistant.anthropic_provider import DEFAULT_MODEL, AnthropicProvider, Effort
from antares_web_mcp.assistant.provider import ChatProvider, ProviderError

ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"


def _build_anthropic(model: str | None, effort: Effort) -> ChatProvider:
    api_key = os.environ.get(ANTHROPIC_API_KEY_ENV)
    if not api_key:
        raise ProviderError(
            f"No Anthropic API key: set `assistant.anthropic_api_key` in the Antares Web configuration file, "
            f"or the {ANTHROPIC_API_KEY_ENV} environment variable of the server."
        )
    return AnthropicProvider(anthropic.AsyncAnthropic(api_key=api_key), model=model or DEFAULT_MODEL, effort=effort)


PROVIDERS: dict[str, Callable[[str | None, Effort], ChatProvider]] = {"anthropic": _build_anthropic}


def build_provider(name: str, *, model: str | None, effort: Effort) -> ChatProvider:
    builder = PROVIDERS.get(name)
    if builder is None:
        raise ProviderError(f"Unknown provider '{name}'. Available providers: {sorted(PROVIDERS)}.")
    return builder(model, effort)
