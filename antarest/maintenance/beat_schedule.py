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
Celery Beat schedule configuration.

This module configures periodic tasks that will be executed by Beat scheduler.
The schedule is loaded when Beat starts.
"""

import logging

from antarest.celery.app import celery_app

logger = logging.getLogger(__name__)


@celery_app.on_after_configure.connect  # type: ignore[misc]
def setup_periodic_tasks(sender: object, **kwargs: object) -> None:
    """
    Configure periodic tasks.

    This function is called automatically when Beat scheduler starts.
    It registers all periodic maintenance tasks.
    """
    logger.info("Setting up periodic tasks")

    # Import tasks here to avoid circular imports
    from antarest.maintenance.tasks.gc_matrix import clean_matrices_task

    # Matrix Garbage Collector - every 3600 seconds (1 hour)
    sender.add_periodic_task(  # type: ignore[attr-defined]
        3600.0,  # Every hour
        clean_matrices_task.s(),
        name="matrix-gc",
    )

    logger.info("Periodic tasks configured successfully")
