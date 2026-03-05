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
Task action handlers.

Importing this package triggers registration of all handlers
in the TaskActionRegistry.
"""

from antarest.core.tasks.actions import (
    launcher_actions,
    matrix_actions,
    output_actions,
    study_actions,
    variant_actions,
    watcher_actions,
)

__all__ = [
    "launcher_actions",
    "matrix_actions",
    "output_actions",
    "study_actions",
    "variant_actions",
    "watcher_actions",
]
