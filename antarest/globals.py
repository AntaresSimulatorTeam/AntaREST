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

import os

# A unique ID for each worker process, in a multi process environment (gunicorn or any other way)
# The system starting the workers is responsible for defining a value for the env var ANTAREST_WORKER_ID
# Currently, see startup script start.sh, or gunicorn configuration conf/gunicorn.py.
#
# The worker ID may be used a stable ID for metrics or other purposes.
ANTAREST_WORKER_ID: int = int(os.environ.get("ANTAREST_WORKER_ID", 0))
