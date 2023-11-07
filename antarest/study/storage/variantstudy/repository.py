import typing as t

from sqlalchemy.orm import Session  # type: ignore

from antarest.core.interfaces.cache import ICache
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.model import Study
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.variantstudy.model.dbmodel import CommandBlock, VariantStudy


class VariantStudyRepository(StudyMetadataRepository):
    """
    Variant study repository
    """

    def __init__(self, cache_service: ICache, session: t.Optional[Session] = None):
        """
        Initialize the variant study repository.

        Args:
            cache_service: Cache service for the repository.
            session: Optional SQLAlchemy session to be used.
        """
        super().__init__(cache_service)
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

    def get_children(self, parent_id: str) -> t.List[VariantStudy]:
        """
        Get the children of a variant study.

        Args:
            parent_id: Identifier of the parent study.

        Returns:
            List of `VariantStudy` objects.
        """
        studies: t.List[VariantStudy] = (
            self.session.query(VariantStudy).filter(VariantStudy.parent_id == parent_id).all()
        )
        return studies

    def get_all_command_blocks(self) -> t.List[CommandBlock]:
        """
        Get all command blocks.

        Returns:
            List of `CommandBlock` objects.
        """
        cmd_blocks: t.List[CommandBlock] = self.session.query(CommandBlock).all()
        return cmd_blocks
