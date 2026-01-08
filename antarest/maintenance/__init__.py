# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
Maintenance package for AntaREST.

This package contains:
- Celery application configuration (app.py)
- Worker context for dependency injection (context.py)
- Periodic maintenance tasks in tasks/ (garbage collection, archiving, etc.)
"""
