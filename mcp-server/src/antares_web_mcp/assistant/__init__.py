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
Assistant: an AI agent that answers questions about Antares Web studies with the MCP tools.

```
POST /v1/assistant/chat (Antares Web)
        │  starts one process per request: `antares-web-assistant` (runner.py)
        ▼
    agent.py ──── ChatProvider (provider.py) ────▶ model API (anthropic_provider.py)
        │
        └── in-memory MCP client ──▶ MCP tools ──REST, with the user's token──▶ Antares Web
```

Only `anthropic_provider.py` depends on a model vendor: to use another one, implement
`ChatProvider` and register it in `providers.py`.
"""
