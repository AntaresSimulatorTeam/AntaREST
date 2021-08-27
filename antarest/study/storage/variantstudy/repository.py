from typing import Optional, List

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.variantstudy.model.dbmodel import (
    VariantStudy,
    CommandBlock,
)


class VariantStudyRepository(StudyMetadataRepository):
    """
    Variant  study repository
    """

    def get_childs(self, parent_id: str) -> List[VariantStudy]:
        studies: List[VariantStudy] = (
            db.session.query(VariantStudy)
            .filter(VariantStudy.parent_id == parent_id)
            .all()
        )
        return studies

    def get_command(
        self, study_id: str, command_id: str
    ) -> Optional[CommandBlock]:
        command: CommandBlock = (
            db.session.query(CommandBlock)
            .filter(
                CommandBlock.study_id == study_id
                and CommandBlock.id == command_id
            )
            .all()
        )
        return command
