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
import time
from typing import Sequence

from typing_extensions import override

from antarest.core.config import Config
from antarest.core.exceptions import TaskAlreadyRunning
from antarest.core.interfaces.service import IService
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.requests import RequestParameters
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.model import RawStudy, Study
from antarest.study.repository import AccessPermissions, StudyFilter
from antarest.study.service import StudyService
from antarest.study.storage.output_service import OutputService
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy

logger = logging.getLogger(__name__)


class AutoArchiveService(IService):
    def __init__(self, study_service: StudyService, output_service: OutputService, config: Config):
        super(AutoArchiveService, self).__init__()
        self.study_service = study_service
        self.output_service = output_service
        self.config = config
        self.sleep_cycle = self.config.storage.auto_archive_sleeping_time
        self.max_parallel = self.config.storage.auto_archive_max_parallel

    def _try_archive_studies(self) -> None:
        """
        Archive old studies
        Clear old variant snapshots
        """
        old_date = datetime.datetime.utcnow() - datetime.timedelta(days=self.config.storage.auto_archive_threshold_days)
        with db():
            # in this part full `Read` rights over studies are granted to this function
            studies: Sequence[Study] = self.study_service.repository.get_all(
                study_filter=StudyFilter(managed=True, access_permissions=AccessPermissions(is_admin=True))
            )
            # list of study IDs and boolean indicating if it's a raw study (True) or a variant (False)
            study_ids_to_archive = [
                (study.id, isinstance(study, RawStudy))
                for study in studies
                if (study.last_access or study.updated_at) < old_date
                and (isinstance(study, VariantStudy) or not study.archived)
            ]
        for study_id, is_raw_study in study_ids_to_archive[0 : self.max_parallel]:
            try:
                if is_raw_study:
                    logger.info(
                        f"Auto Archiving raw study {study_id} (dry_run: {self.config.storage.auto_archive_dry_run})"
                    )
                    if not self.config.storage.auto_archive_dry_run:
                        with db():
                            self.study_service.archive(
                                study_id,
                                params=RequestParameters(DEFAULT_ADMIN_USER),
                            )
                else:
                    logger.info(
                        f"Auto Archiving variant study {study_id} (dry_run: {self.config.storage.auto_archive_dry_run})"
                    )
                    if not self.config.storage.auto_archive_dry_run:
                        with db():
                            self.output_service.archive_outputs(
                                study_id,
                                params=RequestParameters(DEFAULT_ADMIN_USER),
                            )
            except TaskAlreadyRunning:
                pass
            except Exception as e:
                logger.error(
                    f"Failed to auto archive study {study_id}",
                    exc_info=e,
                )
        with db():
            self.study_service.storage_service.variant_study_service.clear_all_snapshots(
                datetime.timedelta(days=self.config.storage.snapshot_retention_days),
                params=RequestParameters(DEFAULT_ADMIN_USER),
            )

    @override
    def _loop(self) -> None:
        while True:
            try:
                self._try_archive_studies()
            except Exception as e:
                logger.error(
                    "Unexpected error happened when processing auto archive service loop",
                    exc_info=e,
                )
            finally:
                time.sleep(self.sleep_cycle)
