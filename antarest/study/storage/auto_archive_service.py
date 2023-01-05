import datetime
import logging
import time
from typing import List, Tuple

from antarest.core.config import Config
from antarest.core.exceptions import TaskAlreadyRunning
from antarest.core.interfaces.service import IService
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.requests import RequestParameters
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.model import Study, RawStudy
from antarest.study.service import StudyService
from antarest.study.storage.utils import is_managed
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy

logger = logging.getLogger(__name__)


class AutoArchiveService(IService):
    def __init__(self, study_service: StudyService, config: Config):
        super(AutoArchiveService, self).__init__()
        self.study_service = study_service
        self.config = config
        self.sleep_cycle = self.config.storage.auto_archive_sleeping_time
        self.max_parallel = self.config.storage.auto_archive_max_parallel

    def _try_archive_studies(self) -> None:
        now = datetime.datetime.utcnow()
        study_ids_to_archive: List[Tuple[str, bool]] = []
        with db():
            studies: List[Study] = self.study_service.repository.get_all()
            # list of study id and boolean indicating if it's a raw study (True) or a variant (False)
            study_ids_to_archive = [
                (study.id, isinstance(study, RawStudy))
                for study in studies
                if is_managed(study)
                # todo this should be last_access
                and study.updated_at
                < now
                - datetime.timedelta(
                    days=self.config.storage.auto_archive_threshold_days
                )
                and (isinstance(study, VariantStudy) or not study.archived)
            ]
        for study_id, is_raw_study in study_ids_to_archive[
            0 : self.max_parallel
        ]:
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
                            self.study_service.archive_outputs(
                                study_id,
                                params=RequestParameters(DEFAULT_ADMIN_USER),
                            )
                            self.study_service.storage_service.variant_study_service.clear_snapshot(
                                self.study_service.get_study(study_id)
                            )
            except TaskAlreadyRunning:
                pass
            except Exception as e:
                logger.error(
                    f"Failed to auto archive study {study_id}",
                    exc_info=e,
                )

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
