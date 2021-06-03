import logging
from typing import Optional, List

from fastapi_sqlalchemy import db

from antarest.storage.model import Study


class StudyMetadataRepository:
    """
    Database connector to manage Study entity
    """

    def __init__(self) -> None:
        self.logger = logging.Logger(self.__class__.__name__)

    def save(self, metadata: Study) -> Study:
        metadata.groups = [db.session.merge(g) for g in metadata.groups]
        if metadata.owner:
            metadata.owner = db.session.merge(metadata.owner)
        db.session.add(metadata)
        db.session.commit()

        self.logger.debug(f"save study {metadata.id}")
        return metadata

    def get(self, id: str) -> Optional[Study]:
        metadata: Study = db.session.query(Study).get(id)
        return metadata

    def get_all(self) -> List[Study]:
        metadatas: List[Study] = db.session.query(Study).all()
        return metadatas

    def delete(self, id: str) -> None:
        u: Study = db.session.query(Study).get(id)
        db.session.delete(u)
        db.session.commit()

        self.logger.debug(f"delete study {id}")
