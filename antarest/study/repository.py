import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import with_polymorphic  # type: ignore

from antarest.core.interfaces.cache import ICache, CacheConstants
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.model import Study, RawStudy

logger = logging.getLogger(__name__)


class StudyMetadataRepository:
    """
    Database connector to manage Study entity
    """

    def __init__(self, cache_service: ICache):
        self.cache_service = cache_service

    def save(
        self, metadata: Study, update_modification_date: bool = False
    ) -> Study:
        metadata_id = metadata.id or metadata.name
        logger.debug(f"Saving study {metadata_id}")
        if update_modification_date:
            metadata.updated_at = datetime.utcnow()

        metadata.groups = [db.session.merge(g) for g in metadata.groups]
        if metadata.owner:
            metadata.owner = db.session.merge(metadata.owner)
        db.session.add(metadata)
        db.session.commit()

        self._invalidate_study_listing_cache()
        return metadata

    def refresh(self, metadata: Study) -> None:
        db.session.refresh(metadata)

    def get(self, id: str) -> Optional[Study]:
        metadata: Study = db.session.query(Study).get(id)
        return metadata

    def get_all(self) -> List[Study]:
        entity = with_polymorphic(Study, "*")
        metadatas: List[Study] = (
            db.session.query(entity).filter(RawStudy.missing.is_(None)).all()
        )
        return metadatas

    def get_all_raw(self, show_missing: bool = True) -> List[RawStudy]:
        query = db.session.query(RawStudy)
        if not show_missing:
            query = query.filter(RawStudy.missing.is_(None))
        metadatas: List[RawStudy] = query.all()
        return metadatas

    def delete(self, id: str) -> None:
        logger.debug(f"Deleting study {id}")
        u: Study = db.session.query(Study).get(id)
        db.session.delete(u)
        db.session.commit()
        self._invalidate_study_listing_cache()

    def _invalidate_study_listing_cache(self) -> None:
        self.cache_service.invalidate(CacheConstants.STUDY_LISTING.value)
        self.cache_service.invalidate(
            CacheConstants.STUDY_LISTING_SUMMARY.value
        )
        self.cache_service.invalidate(
            CacheConstants.STUDY_LISTING_MANAGED.value
        )
        self.cache_service.invalidate(
            CacheConstants.STUDY_LISTING_SUMMARY_MANAGED.value
        )
