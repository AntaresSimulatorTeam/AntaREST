from typing import Union

from antarest.core.exceptions import StudyTypeUnsupported
from antarest.study.common.studystorage import IStudyStorageService
from antarest.study.model import Study, RawStudy
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from antarest.study.storage.variantstudy.variant_study_service import (
    VariantStudyService,
)


class StudyStorageService:
    def __init__(
        self,
        raw_study_service: RawStudyService,
        variante_study_service: VariantStudyService,
    ):
        self.raw_study_service = raw_study_service
        self.variant_study_service = variante_study_service

    def get_storage(
        self, study: Study
    ) -> IStudyStorageService[Union[RawStudy, VariantStudy]]:
        if isinstance(study, RawStudy):
            return self.raw_study_service
        elif isinstance(study, VariantStudy):
            return self.variant_study_service
        else:
            raise StudyTypeUnsupported(study.id, study.type)
