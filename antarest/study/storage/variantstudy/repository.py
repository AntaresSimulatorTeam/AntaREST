from typing import List

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.variantstudy.model.dbmodel import (
    VariantStudy,
)


class VariantStudyRepository(StudyMetadataRepository):
    """
    Variant  study repository
    """

    def get_children(self, parent_id: str) -> List[VariantStudy]:
        studies: List[VariantStudy] = (
            db.session.query(VariantStudy)
            .filter(VariantStudy.parent_id == parent_id)
            .all()
        )
        return studies
