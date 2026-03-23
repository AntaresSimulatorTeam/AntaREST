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
Auto-archive service for desktop mode.

This service runs as a background thread in desktop mode.
In production (Celery mode), use the auto_archive_task instead.
"""

import logging
import time

from typing_extensions import override

from antarest.core.config import Config
from antarest.core.interfaces.service import IService
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.login.utils import current_user_context
from antarest.maintenance.tasks.auto_archive import archive_old_studies
from antarest.output.service import OutputService
from antarest.study.service import StudyService

logger = logging.getLogger(__name__)


class AutoArchiveService(IService):
    """
    Service for auto-archiving old studies (desktop mode).

    This service maintains backward compatibility with the desktop mode
    by running the archive logic in a background thread.
    The actual logic is delegated to the archive_old_studies function.
    """

    def __init__(self, study_service: StudyService, output_service: OutputService, config: Config):
        super().__init__()
        self.study_service = study_service
        self.output_service = output_service
        self.config = config
        self.sleep_cycle = self.config.storage.auto_archive_sleeping_time

    @override
    def _loop(self) -> None:
        with current_user_context(DEFAULT_ADMIN_USER):
            while True:
                try:
                    result = archive_old_studies(
                        study_service=self.study_service,
                        output_service=self.output_service,
                        threshold_days=self.config.storage.auto_archive_threshold_days,
                        snapshot_retention_days=self.config.storage.snapshot_retention_days,
                        dry_run=self.config.storage.auto_archive_dry_run,
                    )
                    logger.info(
                        f"Auto-archive completed: status={result.status}, archived_studies={result.archived_studies}"
                    )
                except Exception as e:
                    logger.error(
                        "Unexpected error happened when processing auto archive service loop",
                        exc_info=e,
                    )
                finally:
                    time.sleep(self.sleep_cycle)
