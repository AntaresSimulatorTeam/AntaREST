"""
Test the database model.
"""
import uuid

from sqlalchemy import inspect  # type: ignore
from sqlalchemy.engine import Engine  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from antarest.study.model import Study


# noinspection SpellCheckingInspection
class TestStudy:
    """
    Test the study model.
    """

    def test_study(self, db_session: Session) -> None:
        """
        Basic test of the `study` table.
        """
        study_id = uuid.uuid4()

        with db_session:
            db_session.add(Study(id=str(study_id), name="Study 1"))
            db_session.commit()

        with db_session:
            study = db_session.query(Study).first()
            assert study.id == str(study_id)
            assert study.name == "Study 1"

    def test_index_on_study(self, db_engine: Engine) -> None:
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes("study")
        index_names = {index["name"] for index in indexes}
        assert index_names == {
            "ix_study_archived",
            "ix_study_created_at",
            "ix_study_folder",
            "ix_study_name",
            "ix_study_owner_id",
            "ix_study_parent_id",
            "ix_study_type",
            "ix_study_updated_at",
            "ix_study_version",
        }

    def test_index_on_rawstudy(self, db_engine: Engine) -> None:
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes("rawstudy")
        index_names = {index["name"] for index in indexes}
        assert index_names == {"ix_rawstudy_workspace", "ix_rawstudy_missing"}

    def test_index_on_variantstudy(self, db_engine: Engine) -> None:
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes("variantstudy")
        index_names = {index["name"] for index in indexes}
        assert not index_names

    def test_index_on_study_additional_data(self, db_engine: Engine) -> None:
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes("study_additional_data")
        index_names = {index["name"] for index in indexes}
        assert index_names == {"ix_study_additional_data_patch"}
