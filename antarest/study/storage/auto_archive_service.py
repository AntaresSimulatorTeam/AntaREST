import datetime
import logging
import time
from typing import List

from antarest.core.config import Config
from antarest.core.interfaces.service import IService
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.requests import RequestParameters
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

    def _loop(self) -> None:
        while True:
            try:
                now = datetime.datetime.utcnow()
                studies: List[Study] = self.study_service.repository.get_all()
                for study in studies:
                    if is_managed(
                        study
                    ) and study.updated_at < now - datetime.timedelta(
                        days=self.config.storage.auto_archive_threshold_days
                    ):
                        if isinstance(RawStudy, study) and not study.archived:
                            self.study_service.archive(
                                study.id,
                                params=RequestParameters(DEFAULT_ADMIN_USER),
                            )
                        elif isinstance(VariantStudy, study):
                            self.study_service.archive_outputs(
                                study.id,
                                params=RequestParameters(DEFAULT_ADMIN_USER),
                            )
            except Exception as e:
                logger.error(
                    "Unexpected error happened when processing auto archive service loop",
                    exc_info=e,
                )
            finally:
                time.sleep(2)
