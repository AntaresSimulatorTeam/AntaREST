from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.core.config import Config, StorageConfig, WorkspaceConfig
from antarest.core.exceptions import StudyNotFoundError, VariantGenerationError
from antarest.core.interfaces.cache import CacheConstants
from antarest.core.jwt import JWTUser
from antarest.core.model import PublicMode
from antarest.core.requests import RequestParameters
from antarest.core.tasks.model import TaskDTO, TaskResult, TaskStatus
from antarest.login.model import User
from antarest.study.model import DEFAULT_WORKSPACE_NAME, StudyAdditionalData
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.dbmodel import CommandBlock, VariantStudy
from antarest.study.storage.variantstudy.repository import VariantStudyRepository
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService


def build_config(study_path: Path):
    return Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig(path=study_path)}))


@pytest.mark.unit_test
def test_get(tmp_path: str, project_path) -> None:
    """
    path_to_studies
    |_study1 (d)
    |_ study2.py
        |_ settings (d)
    |_myfile (f)
    """

    # Create folders
    path_to_studies = Path(tmp_path)
    (path_to_studies / "study1").mkdir()
    (path_to_studies / "myfile").touch()
    path_study = path_to_studies / "study2.py"
    path_study.mkdir()
    (path_study / "settings").mkdir()
    (path_study / "study.antares").touch()

    data = {"titi": 43}
    sub_route = "settings"

    path = path_study / "settings"
    key = "titi"

    study = Mock()
    study.get.return_value = data
    study_factory = Mock()
    study_factory.create_from_fs.return_value = FileStudy(Mock(), study)

    study_service = VariantStudyService(
        raw_study_service=Mock(),
        cache=Mock(),
        task_service=Mock(),
        command_factory=Mock(),
        study_factory=study_factory,
        config=build_config(path_to_studies),
        repository=Mock(),
        event_bus=Mock(),
        patch_service=Mock(),
    )

    metadata = VariantStudy(id="study2.py", path=str(path_study), generation_task="1")
    study_service.exists = Mock()
    study_service.exists.return_value = False

    def task_status(*args):
        for t in [
            TaskDTO(
                id="1",
                name="generation task",
                owner=None,
                status=TaskStatus.RUNNING,
                creation_date_utc="",
                completion_date_utc=None,
                result=None,
            ),
            TaskDTO(
                id="1",
                name="generation task",
                owner=None,
                status=TaskStatus.COMPLETED,
                creation_date_utc="",
                completion_date_utc=None,
                result=TaskResult(success=False, message=""),
            ),
        ]:
            yield t

    study_service.task_service.status_task.side_effect = task_status()
    with pytest.raises(VariantGenerationError, match="Error while generating study2.py"):
        study_service.get(metadata=metadata, url=sub_route, depth=2)
    study_service.task_service.await_task.assert_called()

    study_service.exists.return_value = True
    output = study_service.get(metadata=metadata, url=sub_route, depth=2, format="json")

    assert output == data

    study.get.assert_called_once_with(["settings"], depth=2, format="json")


@pytest.mark.unit_test
def test_get_cache(tmp_path: str) -> None:
    # Create folders
    path_to_studies = Path(tmp_path)
    (path_to_studies / "study1").mkdir()
    (path_to_studies / "myfile").touch()
    path_study = path_to_studies / "study2.py"
    path_study.mkdir()
    (path_study / "settings").mkdir()
    (path_study / "study.antares").touch()
    path = path_study / "settings"

    data = {"titi": 43}
    study = Mock()
    study.get.return_value = data

    study_factory = Mock()
    study_factory.create_from_fs.return_value = FileStudy(Mock(), study)

    cache = Mock()
    cache.get.return_value = None

    study_service = VariantStudyService(
        raw_study_service=Mock(),
        cache=cache,
        task_service=Mock(),
        command_factory=Mock(),
        study_factory=study_factory,
        config=Mock(),
        repository=Mock(),
        event_bus=Mock(),
        patch_service=Mock(),
    )

    metadata = VariantStudy(id="study2.py", path=str(path_study))

    cache_id = f"{CacheConstants.RAW_STUDY}/{metadata.id}"
    study_service.exists = Mock()
    study_service.exists.return_value = True

    assert study_service.get(metadata=metadata, url="", depth=-1) == data
    cache.get.assert_called_with(cache_id)
    cache.put.assert_called_with(cache_id, data)

    cache.get.return_value = data
    assert study_service.get(metadata=metadata, url="", depth=-1) == data
    cache.get.assert_called_with(cache_id)


@pytest.mark.unit_test
def test_assert_study_exist(tmp_path: str, project_path) -> None:
    tmp = Path(tmp_path)
    (tmp / "study1").mkdir()
    (tmp / "study.antares").touch()
    path_study2 = tmp / "study2.py"
    path_study2.mkdir()
    (path_study2 / "settings").mkdir()
    (path_study2 / "study.antares").touch()
    # Input
    study_name = "study2.py"
    path_to_studies = Path(tmp_path)

    # Test & Verify
    study_service = VariantStudyService(
        raw_study_service=Mock(),
        cache=Mock(),
        task_service=Mock(),
        command_factory=Mock(),
        study_factory=Mock(),
        config=build_config(path_to_studies),
        repository=Mock(),
        event_bus=Mock(),
        patch_service=Mock(),
    )

    metadata = VariantStudy(id=study_name, path=str(path_study2))

    study_service.exists = Mock()
    study_service.exists.return_value = True
    study_service._check_study_exists(metadata)


@pytest.mark.unit_test
def test_assert_study_not_exist(tmp_path: str, project_path) -> None:
    # Create folders
    tmp = Path(tmp_path)
    (tmp / "study1").mkdir()
    (tmp / "myfile").touch()
    path_study2 = tmp / "study2.py"
    path_study2.mkdir()
    (path_study2 / "settings").mkdir()

    # Input
    study_name = "study3"
    path_to_studies = Path(tmp_path)

    # Test & Verify
    study_service = VariantStudyService(
        raw_study_service=Mock(),
        cache=Mock(),
        task_service=Mock(),
        command_factory=Mock(),
        study_factory=Mock(),
        config=build_config(path_to_studies),
        repository=Mock(),
        event_bus=Mock(),
        patch_service=Mock(),
    )

    metadata = VariantStudy(id=study_name, path=str(path_study2))

    study_service.exists = Mock()
    study_service.exists.return_value = False

    with pytest.raises(StudyNotFoundError):
        study_service._check_study_exists(metadata)


@pytest.mark.unit_test
def test_copy_study() -> None:
    study_service = VariantStudyService(
        raw_study_service=Mock(),
        cache=Mock(),
        task_service=Mock(),
        command_factory=Mock(),
        study_factory=Mock(),
        config=build_config(Path("")),
        repository=Mock(),
        event_bus=Mock(),
        patch_service=Mock(),
    )

    src_id = "source"
    commands = [
        CommandBlock(
            study_id=src_id,
            command="Command",
            args="",
            index=0,
            version=7,
        )
    ]
    src_md = VariantStudy(
        id=src_id,
        path="path",
        commands=commands,
        additional_data=StudyAdditionalData(),
    )

    md = study_service.copy(src_md, "dst_name", [])
    assert len(src_md.commands) == len(md.commands)


@pytest.mark.unit_test
def test_delete_study(tmp_path: Path) -> None:
    name = "my-study"
    study_path = tmp_path / name
    study_path.mkdir()
    (study_path / "study.antares").touch()

    cache = Mock()

    study_service = VariantStudyService(
        raw_study_service=Mock(),
        cache=cache,
        task_service=Mock(),
        command_factory=Mock(),
        study_factory=Mock(),
        config=build_config(tmp_path),
        repository=Mock(),
        event_bus=Mock(),
        patch_service=Mock(),
    )

    md = VariantStudy(id=name, path=str(study_path))

    study_service.delete(md)
    cache.invalidate_all.assert_called_once_with(
        [
            f"{CacheConstants.RAW_STUDY}/{name}",
            f"{CacheConstants.STUDY_FACTORY}/{name}",
        ]
    )
    assert not study_path.exists()


@pytest.mark.unit_test
def test_get_variant_children(tmp_path: Path) -> None:
    name = "my-study"
    study_path = tmp_path / name
    study_path.mkdir()
    (study_path / "study.antares").touch()

    cache = Mock()
    repo_mock = Mock(spec=VariantStudyRepository)
    study_service = VariantStudyService(
        raw_study_service=Mock(),
        cache=cache,
        task_service=Mock(),
        command_factory=Mock(),
        study_factory=Mock(),
        config=build_config(tmp_path),
        repository=repo_mock,
        event_bus=Mock(),
        patch_service=Mock(),
    )

    parent = VariantStudy(
        id="parent",
        name="parent",
        type="variant",
        archived=False,
        path=str(study_path),
        version="700",
        owner=User(id=2, name="me"),
        groups=[],
        public_mode=PublicMode.NONE,
        additional_data=StudyAdditionalData(),
    )
    children = [
        VariantStudy(
            id="child1",
            name="child1",
            type="variant",
            archived=False,
            path=str(study_path),
            version="700",
            owner=User(id=2, name="me"),
            groups=[],
            public_mode=PublicMode.NONE,
            additional_data=StudyAdditionalData(),
        ),
        VariantStudy(
            id="child2",
            name="child2",
            type="variant",
            archived=False,
            path=str(study_path),
            version="700",
            owner=User(id=3, name="not me"),
            groups=[],
            public_mode=PublicMode.NONE,
            additional_data=StudyAdditionalData(),
        ),
    ]
    repo_mock.get.side_effect = [parent] + children
    repo_mock.get_children.side_effect = [children, [], []]

    tree = study_service.get_all_variants_children(
        "parent",
        RequestParameters(user=JWTUser(id=2, type="user", impersonator=2)),
    )
    assert len(tree.children) == 1


@pytest.mark.unit_test
def test_initialize_additional_data(tmp_path: Path) -> None:
    name = "my-study"
    study_path = tmp_path / name
    study_path.mkdir()
    (study_path / "study.antares").touch()

    md = VariantStudy(id=name, path=str(study_path))

    additional_data = StudyAdditionalData(horizon=2050, patch="{}", author="Zoro")

    study_factory = Mock()
    study_factory.create_from_fs.return_value = md

    variant_study_service = VariantStudyService(
        raw_study_service=Mock(),
        cache=Mock(),
        task_service=Mock(),
        command_factory=Mock(),
        study_factory=study_factory,
        config=build_config(tmp_path),
        repository=Mock(spec=VariantStudyRepository),
        event_bus=Mock(),
        patch_service=Mock(),
    )

    variant_study_service._read_additional_data_from_files = Mock(return_value=additional_data)

    variant_study_service.exists = Mock(return_value=False)

    assert variant_study_service.initialize_additional_data(md)
    assert md.additional_data == StudyAdditionalData()

    variant_study_service.exists = Mock(return_value=True)
    assert variant_study_service.initialize_additional_data(md)
    assert md.additional_data == additional_data

    variant_study_service._read_additional_data_from_files.side_effect = FileNotFoundError()

    assert not variant_study_service.initialize_additional_data(md)
