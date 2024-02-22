import datetime
import enum
import typing as t

from pydantic import BaseModel, NonNegativeInt
from sqlalchemy import func, not_, or_  # type: ignore
from sqlalchemy.orm import Session, joinedload, with_polymorphic  # type: ignore

from antarest.core.interfaces.cache import ICache
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import Group
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy, Study, StudyAdditionalData, Tag


def escape_like(string: str, escape_char: str = "\\") -> str:
    """
    Escape the string parameter used in SQL LIKE expressions.

    Examples::

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


class StudyFilter(BaseModel, frozen=True, extra="forbid"):
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
        study_ids: study IDs to filter by
        exists: if raw study missing
        workspace: optional workspace of the study
        folder: optional folder prefix of the study
    """

    name: str = ""
    managed: t.Optional[bool] = None
    archived: t.Optional[bool] = None
    variant: t.Optional[bool] = None
    versions: t.Sequence[str] = ()
    users: t.Sequence[int] = ()
    groups: t.Sequence[str] = ()
    tags: t.Sequence[str] = ()
    study_ids: t.Sequence[str] = ()
    exists: t.Optional[bool] = None
    workspace: str = ""
    folder: str = ""


class StudySortBy(str, enum.Enum):
    """How to sort the results of studies query results"""

    NAME_ASC = "+name"
    NAME_DESC = "-name"
    DATE_ASC = "+date"
    DATE_DESC = "-date"


class StudyPagination(BaseModel, frozen=True, extra="forbid"):
    """
    Pagination of a studies query results

    Attributes:
        page_nb: offset
        page_size: SQL limit
    """

    page_nb: NonNegativeInt = 0
    page_size: NonNegativeInt = 0


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
    ) -> Study:
        if update_modification_date:
            metadata.updated_at = datetime.datetime.utcnow()

        session = self.session
        metadata.groups = [session.merge(g) for g in metadata.groups]
        if metadata.owner:
            metadata.owner = session.merge(metadata.owner)
        session.add(metadata)
        session.commit()

        return metadata

    def refresh(self, metadata: Study) -> None:
        self.session.refresh(metadata)

    def get(self, study_id: str) -> t.Optional[Study]:
        """Get the study by ID or return `None` if not found in database."""
        # todo: I think we should use a `entity = with_polymorphic(Study, "*")`
        #  to make sure RawStudy and VariantStudy fields are also fetched.
        #  see: antarest.study.service.StudyService.delete_study
        # When we fetch a study, we also need to fetch the associated owner and groups
        # to check the permissions of the current user efficiently.
        study: Study = (
            self.session.query(Study)
            .options(joinedload(Study.owner))
            .options(joinedload(Study.groups))
            .options(joinedload(Study.tags))
            .get(study_id)
        )
        return study

    def one(self, study_id: str) -> Study:
        """Get the study by ID or raise `sqlalchemy.exc.NoResultFound` if not found in database."""
        # todo: I think we should use a `entity = with_polymorphic(Study, "*")`
        #  to make sure RawStudy and VariantStudy fields are also fetched.
        #  see: antarest.study.service.StudyService.delete_study
        # When we fetch a study, we also need to fetch the associated owner and groups
        # to check the permissions of the current user efficiently.
        study: Study = (
            self.session.query(Study)
            .options(joinedload(Study.owner))
            .options(joinedload(Study.groups))
            .options(joinedload(Study.tags))
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
        sort_by: t.Optional[StudySortBy] = None,
        pagination: StudyPagination = StudyPagination(),
    ) -> t.Sequence[Study]:
        """
        Retrieve studies based on specified filters, sorting, and pagination.

        Args:
            study_filter: composed of all filtering criteria.
            sort_by: how the user would like the results to be sorted.
            pagination: specifies the number of results to displayed in each page and the actually displayed page.

        Returns:
            The matching studies in proper order and pagination.
        """
        # When we fetch a study, we also need to fetch the associated owner and groups
        # to check the permissions of the current user efficiently.
        # We also need to fetch the additional data to display the study information
        # efficiently (see: `AbstractStorageService.get_study_information`)
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
        q = q.options(joinedload(entity.tags))
        if study_filter.managed is not None:
            if study_filter.managed:
                q = q.filter(or_(entity.type == "variantstudy", RawStudy.workspace == DEFAULT_WORKSPACE_NAME))
            else:
                q = q.filter(entity.type == "rawstudy")
                q = q.filter(RawStudy.workspace != DEFAULT_WORKSPACE_NAME)
        if study_filter.study_ids:
            q = q.filter(entity.id.in_(study_filter.study_ids))
        if study_filter.users:
            q = q.filter(entity.owner_id.in_(study_filter.users))
        if study_filter.groups:
            q = q.join(entity.groups).filter(Group.id.in_(study_filter.groups))
        if study_filter.tags:
            upper_tags = [tag.upper() for tag in study_filter.tags]
            q = q.join(entity.tags).filter(func.upper(Tag.label).in_(upper_tags))
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

        if sort_by:
            if sort_by == StudySortBy.DATE_DESC:
                q = q.order_by(entity.created_at.desc())
            elif sort_by == StudySortBy.DATE_ASC:
                q = q.order_by(entity.created_at.asc())
            elif sort_by == StudySortBy.NAME_DESC:
                q = q.order_by(func.upper(entity.name).desc())
            elif sort_by == StudySortBy.NAME_ASC:
                q = q.order_by(func.upper(entity.name).asc())
            else:
                raise NotImplementedError(sort_by)

        # pagination
        if pagination.page_nb or pagination.page_size:
            q = q.offset(pagination.page_nb * pagination.page_size).limit(pagination.page_size)

        studies: t.Sequence[Study] = q.all()
        return studies

    def get_all_raw(self, exists: t.Optional[bool] = None) -> t.Sequence[RawStudy]:
        query = self.session.query(RawStudy)
        if exists is not None:
            if exists:
                query = query.filter(RawStudy.missing.is_(None))
            else:
                query = query.filter(not_(RawStudy.missing.is_(None)))
        studies: t.Sequence[RawStudy] = query.all()
        return studies

    def delete(self, id_: str, *ids: str) -> None:
        ids = (id_,) + ids
        session = self.session
        session.query(Study).filter(Study.id.in_(ids)).delete(synchronize_session=False)
        session.commit()

    def update_tags(self, study: Study, new_tags: t.Sequence[str]) -> None:
        """
        Updates the tags associated with a given study in the database,
        replacing existing tags with new ones (case-insensitive).

        Args:
            study: The pre-existing study to be updated with the new tags.
            new_tags: The new tags to be associated with the input study in the database.
        """
        new_upper_tags = {tag.upper(): tag for tag in new_tags}
        existing_tags = self.session.query(Tag).filter(func.upper(Tag.label).in_(new_upper_tags)).all()
        for tag in existing_tags:
            if tag.label.upper() in new_upper_tags:
                new_upper_tags.pop(tag.label.upper())
        study.tags = [Tag(label=tag) for tag in new_upper_tags.values()] + existing_tags
        self.session.merge(study)
        self.session.commit()
        # Delete any tag that is not associated with any study.
        # Note: If tags are to be associated with objects other than Study, this code must be updated.
        self.session.query(Tag).filter(~Tag.studies.any()).delete(synchronize_session=False)  # type: ignore
        self.session.commit()

    def list_duplicates(self) -> t.List[t.Tuple[str, str]]:
        """
        Get list of duplicates as tuples (id, path).
        """
        session = self.session
        subquery = session.query(Study.path).group_by(Study.path).having(func.count() > 1).subquery()
        query = session.query(Study.id, Study.path).filter(Study.path.in_(subquery))
        return t.cast(t.List[t.Tuple[str, str]], query.all())
