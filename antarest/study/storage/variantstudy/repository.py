from typing import List

from antarest.core.interfaces.cache import ICache
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.variantstudy.model.dbmodel import CommandBlock, VariantStudy


class VariantStudyRepository(StudyMetadataRepository):
    """
    Variant  study repository
    """

    def __init__(self, cache_service: ICache):
        super().__init__(cache_service)

    def get_children(self, parent_id: str) -> List[VariantStudy]:
        studies: List[VariantStudy] = (
            db.session.query(VariantStudy)
            .filter(VariantStudy.parent_id == parent_id)
            .all()
        )
        return studies

    def get_all_commandblocks(self) -> List[CommandBlock]:
        outputs = db.session.query(CommandBlock).all()

        # for mypy
        assert isinstance(outputs, list)
        for output in outputs:
            assert isinstance(output, CommandBlock)

        return outputs
