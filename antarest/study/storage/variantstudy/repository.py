from datetime import datetime
from typing import List

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.variantstudy.model.dbmodel import (
    VariantStudy, CommandBlock,
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

    def save_command(self, metadata: VariantStudy, command: CommandBlock) -> CommandBlock:
        metadata.updated_at = datetime.now()
        db.session.add(command)
        db.session.add(metadata)
        db.session.commit()
        return command

    def get_commands(self, study_id: str) -> List[CommandBlock]:
        commands: List[CommandBlock] = (
            db.session.query(CommandBlock)
            .filter(CommandBlock.study_id == study_id)
            .all()
        )
        return commands