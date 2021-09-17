import logging
from datetime import datetime
from typing import Optional, List

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.model import Study

logger = logging.getLogger(__name__)


class StudyMetadataRepository:
    """
    Database connector to manage Study entity
    """

    def save(
        self, metadata: Study, update_modification_date: bool = False
    ) -> Study:

        if update_modification_date:
            metadata.updated_at = datetime.now()

        metadata.groups = [db.session.merge(g) for g in metadata.groups]
        if metadata.owner:
            metadata.owner = db.session.merge(metadata.owner)
        db.session.add(metadata)
        db.session.commit()

        logger.debug(f"save study {metadata.id}")
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

        logger.debug(f"delete study {id}")
