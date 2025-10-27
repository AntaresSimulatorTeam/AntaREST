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

import datetime
import logging
import sys
import time
from typing import Sequence

from typing_extensions import override

from antarest.core.config import Config
from antarest.core.exceptions import TaskAlreadyRunning
from antarest.core.interfaces.service import IService
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.utils import current_user_context
from antarest.study.model import RawStudy, Study
from antarest.study.repository import AccessPermissions, StudyFilter
from antarest.study.service import StudyService
from antarest.study.storage.output_service import OutputService
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy

logger = logging.getLogger(__name__)


class AutoArchiveService(IService):
    def __init__(self, study_service: StudyService, output_service: OutputService, config: Config):
        super(AutoArchiveService, self).__init__()
        print("[AUTO-ARCHIVER] Initializing service...", file=sys.stderr, flush=True)
        self.study_service = study_service
        self.output_service = output_service
        self.config = config
        self.sleep_cycle = 60
        self.max_parallel = 5

        msg = (
            f"AutoArchiveService initialized with: threshold={config.storage.auto_archive_threshold_days} days, "
            f"check_interval={self.sleep_cycle}s, max_parallel={self.max_parallel}, "
            f"dry_run={config.storage.auto_archive_dry_run}"
        )
        print(f"[AUTO-ARCHIVER] {msg}", file=sys.stderr, flush=True)
        logger.info(msg)

    def _try_archive_studies(self) -> None:
        """
        Archive old studies
        Clear old variant snapshots
        """
        old_date = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) - datetime.timedelta(
            days=self.config.storage.auto_archive_threshold_days
        )
        print(
            f"[AUTO-ARCHIVER] Check starting: threshold={self.config.storage.auto_archive_threshold_days} days, "
            f"cutoff_date={old_date.isoformat()}, dry_run={self.config.storage.auto_archive_dry_run}",
            file=sys.stderr, flush=True
        )
        logger.info(
            f"Auto-archive check starting: threshold={self.config.storage.auto_archive_threshold_days} days, "
            f"cutoff_date={old_date.isoformat()}, dry_run={self.config.storage.auto_archive_dry_run}"
        )
        with db():
            # in this part full `Read` rights over studies are granted to this function
            studies: Sequence[Study] = self.study_service.repository.get_all(
                study_filter=StudyFilter(managed=True, access_permissions=AccessPermissions(is_admin=True))
            )
            print(f"[AUTO-ARCHIVER] Found {len(studies)} managed studies to check", file=sys.stderr, flush=True)
            logger.info(f"Found {len(studies)} managed studies to check for archival")

            # list of study IDs and boolean indicating if it's a raw study (True) or a variant (False)
            study_ids_to_archive = [
                (study.id, isinstance(study, RawStudy))
                for study in studies
                if (last_activity := study.last_access or study.updated_at) is not None
                and last_activity < old_date
                and (
                    # Variants: always archive outputs (even if already processed)
                    isinstance(study, VariantStudy)
                    # Raw studies: only archive if not already archived
                    or (isinstance(study, RawStudy) and not study.archived)
                )
            ]

            if len(study_ids_to_archive) == 0:
                print("[AUTO-ARCHIVER] No studies eligible for archiving at this time", file=sys.stderr, flush=True)
                logger.info("No studies eligible for archiving at this time")
            else:
                print(
                    f"[AUTO-ARCHIVER] Found {len(study_ids_to_archive)} studies eligible "
                    f"(will process {min(len(study_ids_to_archive), self.max_parallel)})",
                    file=sys.stderr, flush=True
                )
                logger.info(
                    f"Found {len(study_ids_to_archive)} studies eligible for archiving "
                    f"(will process {min(len(study_ids_to_archive), self.max_parallel)} in this batch)"
                )
        for study_id, is_raw_study in study_ids_to_archive[0 : self.max_parallel]:
            try:
                if is_raw_study:
                    logger.info(
                        f"Auto Archiving raw study {study_id} (dry_run: {self.config.storage.auto_archive_dry_run})"
                    )
                    if not self.config.storage.auto_archive_dry_run:
                        with db():
                            self.study_service.archive(study_id)
                else:
                    logger.info(
                        f"Auto Archiving variant study {study_id} (dry_run: {self.config.storage.auto_archive_dry_run})"
                    )
                    if not self.config.storage.auto_archive_dry_run:
                        with db():
                            self.output_service.archive_outputs(study_id)
            except TaskAlreadyRunning:
                pass
            except Exception as e:
                logger.error(
                    f"Failed to auto archive study {study_id}",
                    exc_info=e,
                )
        with db():
            self.study_service.storage_service.variant_study_service.clear_all_snapshots(
                datetime.timedelta(days=self.config.storage.snapshot_retention_days)
            )

    @override
    def _loop(self) -> None:
        print(f"[AUTO-ARCHIVER] Starting main loop (check every {self.sleep_cycle}s)", file=sys.stderr, flush=True)
        logger.info(f"AutoArchiveService starting main loop (check every {self.sleep_cycle}s)")
        with current_user_context(DEFAULT_ADMIN_USER):
            while True:
                try:
                    print(f"[AUTO-ARCHIVER] Running archive check...", file=sys.stderr, flush=True)
                    self._try_archive_studies()
                except Exception as e:
                    print(f"[AUTO-ARCHIVER] ERROR: {e}", file=sys.stderr, flush=True)
                    logger.error(
                        "Unexpected error happened when processing auto archive service loop",
                        exc_info=e,
                    )
                finally:
                    print(f"[AUTO-ARCHIVER] Sleeping for {self.sleep_cycle}s", file=sys.stderr, flush=True)
                    logger.info(f"AutoArchiveService sleeping for {self.sleep_cycle}s before next check")
                    time.sleep(self.sleep_cycle)
