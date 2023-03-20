import logging
from datetime import datetime
from typing import Optional, List, cast

from sqlalchemy.orm import with_polymorphic  # type: ignore

from antarest.core.interfaces.cache import ICache, CacheConstants
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.common.utils import get_study_information
from antarest.study.model import Study, RawStudy, StudyAdditionalData

logger = logging.getLogger(__name__)


class StudyMetadataRepository:
    """
    Database connector to manage Study entity
    """

    def __init__(self, cache_service: ICache):
        self.cache_service = cache_service

    def save(
        self,
        metadata: Study,
        update_modification_date: bool = False,
        update_in_listing: bool = True,
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

        if update_in_listing:
            self._update_study_from_cache_listing(metadata)
        return metadata

    def refresh(self, metadata: Study) -> None:
        db.session.refresh(metadata)

    def get(self, id: str) -> Optional[Study]:
        """Get the study by ID or return `None` if not found in database."""
        metadata: Study = db.session.query(Study).get(id)
        return metadata

    def one(self, id: str) -> Study:
        """Get the study by ID or raise `sqlalchemy.exc.NoResultFound` if not found in database."""
        study: Study = db.session.query(Study).filter_by(id=id).one()
        return study

    def get_list(self, study_id: List[str]) -> List[Study]:
        studies: List[Study] = (
            db.session.query(Study).where(Study.id.in_(study_id)).all()
        )
        return studies

    def get_additional_data(
        self, study_id: str
    ) -> Optional[StudyAdditionalData]:
        metadata: StudyAdditionalData = db.session.query(
            StudyAdditionalData
        ).get(study_id)
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
        self._remove_study_from_cache_listing(id)

    def _remove_study_from_cache_listing(self, study_id: str) -> None:
        try:
            cached_studies = self.cache_service.get(
                CacheConstants.STUDY_LISTING.value
            )
            if cached_studies:
                if study_id in cached_studies:
                    del cached_studies[study_id]
                self.cache_service.put(
                    CacheConstants.STUDY_LISTING.value, cached_studies
                )
        except Exception as e:
            logger.error("Failed to update study listing cache", exc_info=e)
            try:
                self.cache_service.invalidate(
                    CacheConstants.STUDY_LISTING.value
                )
            except Exception as e:
                logger.error("Failed to invalidate listing cache", exc_info=e)

    def _update_study_from_cache_listing(self, study: Study) -> None:
        try:
            cached_studies = self.cache_service.get(
                CacheConstants.STUDY_LISTING.value
            )
            if cached_studies:
                if isinstance(study, RawStudy) and study.missing is not None:
                    del cached_studies[study.id]
                else:
                    cached_studies[study.id] = get_study_information(study)
                self.cache_service.put(
                    CacheConstants.STUDY_LISTING.value, cached_studies
                )
        except Exception as e:
            logger.error("Failed to update study listing cache", exc_info=e)
            try:
                self.cache_service.invalidate(
                    CacheConstants.STUDY_LISTING.value
                )
            except Exception as e:
                logger.error("Failed to invalidate listing cache", exc_info=e)
