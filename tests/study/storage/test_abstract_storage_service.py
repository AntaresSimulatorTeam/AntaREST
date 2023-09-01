import datetime
import zipfile
from pathlib import Path
from typing import List, Optional
from unittest.mock import Mock, call

from antarest.core.config import Config, StorageConfig
from antarest.core.interfaces.cache import ICache
from antarest.core.model import PublicMode
from antarest.core.requests import RequestParameters
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import Group, User
from antarest.study.model import Study
from antarest.study.storage.abstract_storage_service import AbstractStorageService
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfigDTO
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy, StudyFactory
from tests.helpers import with_db_context


class MyStorageService(AbstractStorageService):
    """
    This class is only defined to test `AbstractStorageService` class PUBLIC methods.
    Abstract methods are not implemented: there are not used or patched with a Mock object.
    """

    def create(self, metadata: Study) -> Study:
        raise NotImplementedError

    def exists(self, metadata: Study) -> bool:
        raise NotImplementedError

    # noinspection SpellCheckingInspection
    def copy(self, src_meta: Study, dest_name: str, groups: List[str], with_outputs: bool = False) -> Study:
        raise NotImplementedError

    def get_raw(
        self,
        metadata: Study,
        use_cache: bool = True,
        output_dir: Optional[Path] = None,
    ) -> FileStudy:
        raise NotImplementedError

    def set_reference_output(self, metadata: Study, output_id: str, status: bool) -> None:
        raise NotImplementedError

    def delete(self, metadata: Study) -> None:
        raise NotImplementedError

    def delete_output(self, metadata: Study, output_id: str) -> None:
        raise NotImplementedError

    def get_study_path(self, metadata: Study) -> Path:
        raise NotImplementedError

    def export_study_flat(
        self,
        metadata: Study,
        dst_path: Path,
        outputs: bool = True,
        output_list_filter: Optional[List[str]] = None,
        denormalize: bool = True,
    ) -> None:
        raise NotImplementedError

    def get_synthesis(self, metadata: Study, params: Optional[RequestParameters] = None) -> FileStudyTreeConfigDTO:
        raise NotImplementedError

    def initialize_additional_data(self, study: Study) -> bool:
        raise NotImplementedError


class TmpCopy(object):
    """A helper object that compares equal if a folder is a "tmp_copy" folder."""

    def __init__(self, tmp_path: Path):
        self.tmp_path = tmp_path

    def __eq__(self, other: Path):
        if isinstance(other, Path) and other.name == "tmp_copy":
            # `is_relative_to` is not available for Python < 3.9
            try:
                other.relative_to(self.tmp_path)
                return True
            except ValueError:
                return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return f"<TmpCopy({self.tmp_path})>"


class TestAbstractStorageService:
    @with_db_context
    def test_export_study(self, tmp_path: Path) -> None:
        tmp_dir = tmp_path / "tmp"
        tmp_dir.mkdir()
        study_path = tmp_path / "My Study"

        service = MyStorageService(
            config=Config(storage=StorageConfig(tmp_dir=tmp_dir)),
            study_factory=Mock(spec=StudyFactory),
            patch_service=Mock(spec=PatchService),
            cache=Mock(spec=ICache),
        )

        ## Prepare database objects

        # noinspection PyArgumentList
        user = User(id=0, name="admin")
        db.session.add(user)
        db.session.commit()

        # noinspection PyArgumentList
        group = Group(id="my-group", name="group")
        db.session.add(group)
        db.session.commit()

        # noinspection PyArgumentList
        metadata = Study(
            name="My Study",
            version="860",
            author="John Smith",
            created_at=datetime.datetime(2023, 7, 19, 16, 45),
            updated_at=datetime.datetime(2023, 7, 27, 8, 15),
            last_access=datetime.datetime.utcnow(),
            public_mode=PublicMode.FULL,
            owner=user,
            groups=[group],
            path=str(study_path),
        )
        db.session.add(metadata)
        db.session.commit()

        ## Check the `export_study` function
        service.export_study_flat = Mock(return_value=None)
        target_path = tmp_path / "export.zip"
        actual = service.export_study(metadata, target_path, outputs=True)
        assert actual == target_path

        ## Check the call to export_study_flat
        assert service.export_study_flat.mock_calls == [call(metadata, TmpCopy(tmp_path), True)]

        ## Check that the ZIP file exist and is valid
        with zipfile.ZipFile(target_path) as zf:
            # Actually, there is nothing is the ZIP file,
            # because the Study files doesn't really exist.
            assert not zf.namelist()
