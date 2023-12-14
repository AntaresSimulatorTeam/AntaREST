import datetime
from pathlib import Path
from unittest.mock import Mock

from antarest.core.config import Config, StorageConfig, WorkspaceConfig
from antarest.core.exceptions import TaskAlreadyRunning
from antarest.core.interfaces.cache import ICache
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.requests import RequestParameters
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy
from antarest.study.repository import StudyMetadataRepository
from antarest.study.service import StudyService
from antarest.study.storage.auto_archive_service import AutoArchiveService
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from tests.helpers import with_db_context


@with_db_context
def test_auto_archival(tmp_path: Path):
    workspace_path = tmp_path / "workspace_test"
    auto_archive_service = AutoArchiveService(
        Mock(spec=StudyService),
        Config(storage=StorageConfig(workspaces={"test": WorkspaceConfig(path=workspace_path)})),
    )

    now = datetime.datetime.now()

    repository = StudyMetadataRepository(cache_service=Mock(spec=ICache))

    # Add some studies in the database
    db_session = repository.session
    db_session.add(RawStudy(id="a", workspace="test", updated_at=now - datetime.timedelta(days=61)))
    db_session.add(RawStudy(id="b", workspace="test", updated_at=now - datetime.timedelta(days=59)))
    db_session.add(RawStudy(id="c", workspace="test", updated_at=now - datetime.timedelta(days=61), archived=True))
    db_session.add(RawStudy(id="d", workspace="test", updated_at=now - datetime.timedelta(days=61), archived=False))
    db_session.add(VariantStudy(id="e", updated_at=now - datetime.timedelta(days=61)))
    db_session.commit()

    auto_archive_service.study_service.repository = repository

    auto_archive_service.study_service.storage_service = Mock()
    auto_archive_service.study_service.storage_service.variant_study_service = Mock()
    auto_archive_service.study_service.archive.side_effect = TaskAlreadyRunning
    auto_archive_service.study_service.get_study.return_value = VariantStudy(
        id="e", updated_at=now - datetime.timedelta(days=61)
    )

    auto_archive_service._try_archive_studies()

    auto_archive_service.study_service.archive.assert_called_once_with(
        "d", params=RequestParameters(DEFAULT_ADMIN_USER)
    )
    auto_archive_service.study_service.storage_service.variant_study_service.clear_snapshot.assert_called_once_with(
        VariantStudy(id="e", updated_at=now - datetime.timedelta(days=61))
    )
    auto_archive_service.study_service.archive_outputs.assert_called_once_with(
        "e", params=RequestParameters(DEFAULT_ADMIN_USER)
    )
