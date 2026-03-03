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

import multiprocessing

if __name__ == "__main__":
    # Freeze support needed for pyinstaller. Important to run it before other imports,
    # because some of them call multiprocessing functions.
    multiprocessing.freeze_support()

    from antarest.worker.archive_worker_service import run_archive_worker

    run_archive_worker()
