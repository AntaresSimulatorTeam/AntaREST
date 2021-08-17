import logging
from typing import Optional, List

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.model import Study
from antarest.study.storage.variantstudy.db.dbmodel import VariantStudy


class VariantStudyRepository:
    """
    Database connector to manage Study entity
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    def save(self, study: VariantStudy) -> VariantStudy:
        study.command_block = [
            db.session.merge(c) for c in study.command_block
        ]
        db.session.add(study)
        db.session.commit()

        self.logger.debug(f"save variant study {study.id}")
        return study

    def get(self, id: str) -> Optional[VariantStudy]:
        study: VariantStudy = db.session.query(VariantStudy).get(id)
        return study

    def get_all(self) -> List[Study]:
        study: List[VariantStudy] = db.session.query(VariantStudy).all()
        return study

    def delete(self, id: str) -> None:
        u: VariantStudy = db.session.query(VariantStudy).get(id)
        db.session.delete(u)
        db.session.commit()

        self.logger.debug(f"delete variant study {id}")
