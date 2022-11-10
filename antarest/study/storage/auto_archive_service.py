import datetime
import logging
import time
from typing import List

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

    def _try_archive_studies(self) -> None:
        now = datetime.datetime.utcnow()
        with db():
            studies: List[Study] = self.study_service.repository.get_all()
            for study in studies:
                if is_managed(
                    study
                ) and study.updated_at < now - datetime.timedelta(
                    days=self.config.storage.auto_archive_threshold_days
                ):
                    study_id = study.id
                    try:
                        if isinstance(study, RawStudy) and not study.archived:
                            self.study_service.archive(
                                study.id,
                                params=RequestParameters(DEFAULT_ADMIN_USER),
                            )
                        elif isinstance(study, VariantStudy):
                            self.study_service.storage_service.variant_study_service.clear_snapshot(
                                study
                            )
                            self.study_service.archive_outputs(
                                study.id,
                                params=RequestParameters(DEFAULT_ADMIN_USER),
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
                time.sleep(600)
