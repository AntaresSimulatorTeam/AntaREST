import datetime
from pathlib import Path
from unittest.mock import Mock, call

from antarest.core.config import Config, StorageConfig, WorkspaceConfig
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.requests import RequestParameters
from antarest.study.model import RawStudy, DEFAULT_WORKSPACE_NAME
from antarest.study.storage.auto_archive_service import AutoArchiveService
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy


def test_auto_archival(tmp_path: Path):
    workspace_path = tmp_path / "workspace_test"
    auto_archive_service = AutoArchiveService(
        Mock(),
        Config(
            storage=StorageConfig(
                workspaces={"test": WorkspaceConfig(path=workspace_path)}
            )
        ),
    )

    now = datetime.datetime.now()

    auto_archive_service.study_service.repository = Mock()
    auto_archive_service.study_service.repository.get_all.return_value = [
        RawStudy(
            id="a",
            workspace="not default",
            updated_at=now - datetime.timedelta(days=61),
        ),
        RawStudy(
            id="b",
            workspace=DEFAULT_WORKSPACE_NAME,
            updated_at=now - datetime.timedelta(days=59),
        ),
        RawStudy(
            id="c",
            workspace=DEFAULT_WORKSPACE_NAME,
            updated_at=now - datetime.timedelta(days=61),
            archived=True,
        ),
        RawStudy(
            id="d",
            workspace=DEFAULT_WORKSPACE_NAME,
            updated_at=now - datetime.timedelta(days=61),
            archived=False,
        ),
        VariantStudy(id="e", updated_at=now - datetime.timedelta(days=61)),
    ]
    auto_archive_service.study_service.storage_service = Mock()
    auto_archive_service.study_service.storage_service.variant_study_service = (
        Mock()
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
