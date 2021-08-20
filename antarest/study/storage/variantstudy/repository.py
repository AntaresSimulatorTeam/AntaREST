import logging
from typing import Optional, List

from sqlalchemy import exists  # type: ignore

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.variantstudy.model.db.dbmodel import CommandBlock  # type: ignore

logger = logging.getLogger(__name__)


class VariantStudyCommandRepository(StudyMetadataRepository):
    """
    Database connector to manage Study entity
    """

    def save_command(self, command: CommandBlock) -> None:
        res = db.session.query(
            exists().where(CommandBlock.id == command.id)
        ).scalar()
        if res:
            db.session.merge(command)
        else:
            db.session.add(command)
        db.session.commit()

        logger.debug(f"save command {command.id}")

    def get_command(self, command_id: str) -> Optional[CommandBlock]:
        block: CommandBlock = db.session.query(CommandBlock).get(command_id)
        return block

    def get_commands(self, study_id: str) -> List[CommandBlock]:
        blocks: List[CommandBlock] = db.session.query(CommandBlock).filter(
            CommandBlock.id == study_id
        )
        return blocks

    def delete_command(self, command_id: str) -> None:
        u: CommandBlock = db.session.query(CommandBlock).get(command_id)
        db.session.delete(u)
        db.session.commit()

        logger.debug(f"delete command {command_id}")
