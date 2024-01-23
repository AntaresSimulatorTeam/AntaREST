import datetime
import enum
import logging
import typing as t

from pydantic import BaseModel, Field
from sqlalchemy import not_, or_  # type: ignore
from sqlalchemy.orm import Session, joinedload, with_polymorphic  # type: ignore

from antarest.core.interfaces.cache import CacheConstants, ICache
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import Group
from antarest.study.common.utils import get_study_information
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy, Study, StudyAdditionalData

logger = logging.getLogger(__name__)


def escape_like(string: str, escape_char: str = "\\") -> str:
    """
    Escape the string parameter used in SQL LIKE expressions.

    Examples:
        from sqlalchemy_utils import escape_like


        query = session.query(User).filter(
            User.name.ilike(escape_like('John'))
        )

    Args:
        string: a string to escape
        escape_char: escape character

    Returns:
        Escaped string.
    """
    return string.replace(escape_char, escape_char * 2).replace("%", escape_char + "%").replace("_", escape_char + "_")


class StudyFilter(BaseModel, frozen=True):
    """Study filter class gathering the main filtering parameters

    Attributes:
        name: optional name regex of the study to match
        managed: indicate if just managed studies should be retrieved
        archived: optional if the study is archived
        variant: optional if the study is raw study
        versions: versions to filter by
        users: users to filter by
        groups: groups to filter by
        tags: tags to filter by
        studies_ids: studies ids to filter by
        exists: if raw study missing
        workspace: optional workspace of the study
        folder: optional folder prefix of the study
    """

    name: str = ""
    managed: t.Optional[bool] = None
    archived: t.Optional[bool] = None
    variant: t.Optional[bool] = None
    versions: t.Sequence[str] = ()
    users: t.Sequence["int"] = ()
    groups: t.Sequence[str] = ()
    tags: t.Sequence[str] = ()
    studies_ids: t.Sequence[str] = ()
    exists: t.Optional[bool] = None
    workspace: str = ""
    folder: str = ""


class StudySortBy(str, enum.Enum):
    """How to sort the results of studies query results"""

    NO_SORT = ""
    NAME_ASC = "+name"
    NAME_DESC = "-name"
    DATE_ASC = "+date"
    DATE_DESC = "-date"


class StudyPagination(BaseModel, frozen=True):
    """
    Pagination of a studies query results

    Attributes:
        page_nb: offset
        page_size: SQL limit
    """

    page_nb: int = 0
    page_size: int = Field(0, ge=0)


class StudyMetadataRepository:
    """
    Database connector to manage Study entity
    """

    def __init__(self, cache_service: ICache, session: t.Optional[Session] = None):
        """
        Initialize the repository.

        Args:
            cache_service: Cache service for the repository.
            session: Optional SQLAlchemy session to be used.
        """
        self.cache_service = cache_service
        self._session = session

    @property
    def session(self) -> Session:
        """
        Get the SQLAlchemy session for the repository.

        Returns:
            SQLAlchemy session.
        """
        if self._session is None:
            # Get or create the session from a context variable (thread local variable)
            return db.session
        # Get the user-defined session
        return self._session

    def save(
        self,
        metadata: Study,
        update_modification_date: bool = False,
        update_in_listing: bool = True,
    ) -> Study:
        metadata_id = metadata.id or metadata.name
        logger.debug(f"Saving study {metadata_id}")
        if update_modification_date:
            metadata.updated_at = datetime.datetime.utcnow()

        session = self.session
        metadata.groups = [session.merge(g) for g in metadata.groups]
        if metadata.owner:
            metadata.owner = session.merge(metadata.owner)
        session.add(metadata)
        session.commit()

        if update_in_listing:
            self._update_study_from_cache_listing(metadata)
        return metadata

    def refresh(self, metadata: Study) -> None:
        self.session.refresh(metadata)

    def get(self, id: str) -> t.Optional[Study]:
        """Get the study by ID or return `None` if not found in database."""
        # When we fetch a study, we also need to fetch the associated owner and groups
        # to check the permissions of the current user efficiently.
        study: Study = (
            # fmt: off
            self.session.query(Study)
            .options(joinedload(Study.owner))
            .options(joinedload(Study.groups))
            .get(id)
            # fmt: on
        )
        return study

    def one(self, study_id: str) -> Study:
        """Get the study by ID or raise `sqlalchemy.exc.NoResultFound` if not found in database."""
        # When we fetch a study, we also need to fetch the associated owner and groups
        # to check the permissions of the current user efficiently.
        study: Study = (
            self.session.query(Study)
            .options(joinedload(Study.owner))
            .options(joinedload(Study.groups))
            .filter_by(id=study_id)
            .one()
        )
        return study

    def get_additional_data(self, study_id: str) -> t.Optional[StudyAdditionalData]:
        study: StudyAdditionalData = self.session.query(StudyAdditionalData).get(study_id)
        return study

    def get_all(
        self,
        study_filter: StudyFilter = StudyFilter(),
        sort_by: StudySortBy = StudySortBy.NO_SORT,
        pagination: StudyPagination = StudyPagination(),
    ) -> t.List[Study]:
        """
        This function goal is to create a search engine throughout the studies with optimal
        runtime.

        Args:
            study_filter: composed of all filtering criteria
            sort_by: how the user would like the results to be sorted
            pagination: specifies the number of results to displayed in each page and the actually displayed page

        Returns:
            The matching studies in proper order and pagination
        """
        # When we fetch a study, we also need to fetch the associated owner and groups
        # to check the permissions of the current user efficiently.
        # We also need to fetch the additional data to display the study information
        # efficiently (see: `utils.get_study_information`)
        entity = with_polymorphic(Study, "*")

        # noinspection PyTypeChecker
        q = self.session.query(entity)
        if study_filter.exists is not None:
            if study_filter.exists:
                q = q.filter(RawStudy.missing.is_(None))
            else:
                q = q.filter(not_(RawStudy.missing.is_(None)))
        q = q.options(joinedload(entity.owner))
        q = q.options(joinedload(entity.groups))
        q = q.options(joinedload(entity.additional_data))
        if study_filter.managed is not None:
            if study_filter.managed:
                q = q.filter(or_(entity.type == "variantstudy", RawStudy.workspace == DEFAULT_WORKSPACE_NAME))
            else:
                q = q.filter(entity.type == "rawstudy")
                q = q.filter(RawStudy.workspace != DEFAULT_WORKSPACE_NAME)
        if study_filter.studies_ids:
            q = q.filter(entity.id.in_(study_filter.studies_ids))
        if study_filter.users:
            q = q.filter(entity.owner_id.in_(study_filter.users))
        if study_filter.groups:
            q = q.join(entity.groups).filter(Group.id.in_(study_filter.groups))
        if study_filter.archived is not None:
            q = q.filter(entity.archived == study_filter.archived)
        if study_filter.name:
            regex = f"%{escape_like(study_filter.name)}%"
            q = q.filter(entity.name.ilike(regex))
        if study_filter.folder:
            regex = f"{escape_like(study_filter.folder)}%"
            q = q.filter(entity.folder.ilike(regex))
        if study_filter.workspace:
            q = q.filter(RawStudy.workspace == study_filter.workspace)
        if study_filter.variant is not None:
            if study_filter.variant:
                q = q.filter(entity.type == "variantstudy")
            else:
                q = q.filter(entity.type == "rawstudy")
        if study_filter.versions:
            q = q.filter(entity.version.in_(study_filter.versions))

        # sorting
        if sort_by != StudySortBy.NO_SORT:
            if sort_by == StudySortBy.DATE_DESC:
                q = q.order_by(entity.created_at.desc())
            elif sort_by == StudySortBy.DATE_ASC:
                q = q.order_by(entity.created_at.asc())
            elif sort_by == StudySortBy.NAME_DESC:
                q = q.order_by(entity.name.desc())
            elif sort_by == StudySortBy.NAME_ASC:
                q = q.order_by(entity.name.asc())
            else:
                raise NotImplementedError(sort_by)

        # pagination
        if pagination.page_nb or pagination.page_size:
            q = q.offset(pagination.page_nb * pagination.page_size).limit(pagination.page_size)

        studies: t.List[Study] = q.all()
        return studies

    def get_all_raw(self, exists: t.Optional[bool] = None) -> t.List[RawStudy]:
        query = self.session.query(RawStudy)
        if exists is not None:
            if exists:
                query = query.filter(RawStudy.missing.is_(None))
            else:
                query = query.filter(not_(RawStudy.missing.is_(None)))
        studies: t.List[RawStudy] = query.all()
        return studies

    def delete(self, id: str) -> None:
        logger.debug(f"Deleting study {id}")
        session = self.session
        u: Study = session.query(Study).get(id)
        session.delete(u)
        session.commit()
        self._remove_study_from_cache_listing(id)

    def _remove_study_from_cache_listing(self, study_id: str) -> None:
        try:
            cached_studies = self.cache_service.get(CacheConstants.STUDY_LISTING.value)
            if cached_studies:
                if study_id in cached_studies:
                    del cached_studies[study_id]
                self.cache_service.put(CacheConstants.STUDY_LISTING.value, cached_studies)
        except Exception as e:
            logger.error("Failed to update study listing cache", exc_info=e)
            try:
                self.cache_service.invalidate(CacheConstants.STUDY_LISTING.value)
            except Exception as e:
                logger.error("Failed to invalidate listing cache", exc_info=e)

    def _update_study_from_cache_listing(self, study: Study) -> None:
        try:
            cached_studies = self.cache_service.get(CacheConstants.STUDY_LISTING.value)
            if cached_studies:
                if isinstance(study, RawStudy) and study.missing is not None:
                    del cached_studies[study.id]
                else:
                    cached_studies[study.id] = get_study_information(study)
                self.cache_service.put(CacheConstants.STUDY_LISTING.value, cached_studies)
        except Exception as e:
            logger.error("Failed to update study listing cache", exc_info=e)
            try:
                self.cache_service.invalidate(CacheConstants.STUDY_LISTING.value)
            except Exception as e:
                logger.error("Failed to invalidate listing cache", exc_info=e)
