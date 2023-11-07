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

    def get_ancestor_or_self_ids(self, variant_id: str) -> t.Sequence[str]:
        """
        Retrieve the list of ancestor variant identifiers, including the `variant_id`,
        its parent, and all predecessors of the parent, up to and including the ID
        of the root study (`RawStudy`).

        Args:
            variant_id: Unique identifier of the child variant.

        Returns:
            Ordered list of study identifiers.
        """
        # see: [Recursive Queries](https://www.postgresql.org/docs/current/queries-with.html#QUERIES-WITH-RECURSIVE)
        top_q = self.session.query(Study.id, Study.parent_id)
        top_q = top_q.filter(Study.id == variant_id)
        top_q = top_q.cte("study_cte", recursive=True)

        bot_q = self.session.query(Study.id, Study.parent_id)
        bot_q = bot_q.join(top_q, Study.id == top_q.c.parent_id)

        recursive_q = top_q.union_all(bot_q)
        q = self.session.query(recursive_q)
        return [r[0] for r in q]

    def get_all_command_blocks(self) -> t.List[CommandBlock]:
        """
        Get all command blocks.

        Returns:
            List of `CommandBlock` objects.
        """
        cmd_blocks: t.List[CommandBlock] = self.session.query(CommandBlock).all()
        return cmd_blocks
