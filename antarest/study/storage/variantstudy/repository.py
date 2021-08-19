import logging
from typing import Optional, List

from sqlalchemy import exists  # type: ignore

from antarest.core.utils.fastapi_sqlalchemy import db  # type: ignore
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.variantstudy.db.dbmodel import CommandBlock

logger = logging.getLogger(__name__)


class VariantStudyCommandRepository(StudyMetadataRepository):
    """
    Database connector to manage Study entity
    """

    @staticmethod
    def save_command(command: CommandBlock) -> None:
        res = db.session.query(
            exists().where(CommandBlock.id == command.id)
        ).scalar()
        if res:
            db.session.merge(command)
        else:
            db.session.add(command)
        db.session.commit()

        logger.debug(f"save command {command.id}")

    @staticmethod
    def get_command(command_id: str) -> Optional[CommandBlock]:
        block: CommandBlock = db.session.query(CommandBlock).get(command_id)
        return block

    @staticmethod
    def get_commands(study_id: str) -> List[CommandBlock]:
        blocks: List[CommandBlock] = db.session.query(CommandBlock).filter(
            CommandBlock.id == study_id
        )
        return blocks

    @staticmethod
    def delete_command(command_id: str) -> None:
        u: CommandBlock = db.session.query(CommandBlock).get(command_id)
        db.session.delete(u)
        db.session.commit()

        logger.debug(f"delete command {command_id}")
