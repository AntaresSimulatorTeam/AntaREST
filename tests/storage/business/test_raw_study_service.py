import datetime
import os
import re
from pathlib import Path
from typing import Callable
from unittest.mock import Mock

import pytest

from antarest.core.config import Config, StorageConfig, WorkspaceConfig
from antarest.core.exceptions import (
    StudyNotFoundError,
)
from antarest.core.interfaces.cache import CacheConstants
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy
from antarest.study.storage.rawstudy.raw_study_service import (
    RawStudyService,
)
from antarest.study.storage.utils import get_default_workspace_path


def build_config(study_path: Path):
    return Config(
        storage=StorageConfig(
            workspaces={
                DEFAULT_WORKSPACE_NAME: WorkspaceConfig(path=study_path)
            }
        )
    )


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
    study_factory.create_from_fs.return_value = (None, study)

    study_service = RawStudyService(
        config=build_config(path_to_studies),
        cache=Mock(),
        study_factory=study_factory,
        path_resources=project_path / "resources",
        patch_service=Mock(),
    )

    metadata = RawStudy(
        id="study2.py", workspace=DEFAULT_WORKSPACE_NAME, path=str(path_study)
    )
    output = study_service.get(metadata=metadata, url=sub_route, depth=2)

    assert output == data

    study.get.assert_called_once_with(["settings"], depth=2, formatted=True)


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
    study_factory.create_from_fs.return_value = (None, study)

    cache = Mock()
    cache.get.return_value = None

    metadata = RawStudy(
        id="study2.py", workspace=DEFAULT_WORKSPACE_NAME, path=str(path_study)
    )
    study_service = RawStudyService(
        config=Mock(),
        cache=cache,
        study_factory=study_factory,
        path_resources="",
        patch_service=Mock(),
    )

    cache_id = f"{metadata.id}/{CacheConstants.RAW_STUDY}"
    assert study_service.get(metadata=metadata, url="", depth=-1) == data
    cache.get.assert_called_with(cache_id)
    cache.put.assert_called_with(cache_id, data)

    cache.get.return_value = data
    assert study_service.get(metadata=metadata, url="", depth=-1) == data
    cache.get.assert_called_with(cache_id)


@pytest.mark.unit_test
def test_check_errors():
    study = Mock()
    study.check_errors.return_value = ["Hello"]

    factory = Mock()
    factory.create_from_fs.return_value = None, study
    config = build_config(Path())
    study_service = RawStudyService(
        config=config,
        cache=Mock(),
        study_factory=factory,
        path_resources=Path(),
        patch_service=Mock(),
    )

    metadata = RawStudy(
        id="study",
        workspace=DEFAULT_WORKSPACE_NAME,
        path=str(get_default_workspace_path(config) / "study"),
    )
    assert study_service.check_errors(metadata) == ["Hello"]


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
    study_service = RawStudyService(
        config=build_config(path_to_studies),
        cache=Mock(),
        study_factory=Mock(),
        path_resources=project_path / "resources",
        patch_service=Mock(),
    )

    metadata = RawStudy(
        id=study_name, workspace=DEFAULT_WORKSPACE_NAME, path=str(path_study2)
    )
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
    study_service = RawStudyService(
        config=build_config(path_to_studies),
        cache=Mock(),
        study_factory=Mock(),
        path_resources=project_path / "resources",
        patch_service=Mock(),
    )

    metadata = RawStudy(
        id=study_name, workspace=DEFAULT_WORKSPACE_NAME, path=str(path_study2)
    )
    with pytest.raises(StudyNotFoundError):
        study_service._check_study_exists(metadata)


@pytest.mark.unit_test
def test_create_study(tmp_path: str, project_path) -> None:
    path_studies = Path(tmp_path)

    study = Mock()
    data = {"antares": {"caption": None}}
    study.get.return_value = data

    study_factory = Mock()
    study_factory.create_from_fs.return_value = (None, study)
    config = build_config(path_studies)
    study_service = RawStudyService(
        config=config,
        cache=Mock(),
        study_factory=study_factory,
        path_resources=project_path / "resources",
        patch_service=Mock(),
    )

    metadata = RawStudy(
        id="study1",
        workspace=DEFAULT_WORKSPACE_NAME,
        path=str(get_default_workspace_path(config) / "study1"),
        version=720,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )
    md = study_service.create(metadata)

    assert md.path == f"{tmp_path}{os.sep}study1"
    path_study = path_studies / md.id
    assert path_study.exists()

    path_study_antares_infos = path_study / "study.antares"
    assert path_study_antares_infos.is_file()


@pytest.mark.unit_test
def test_create_study_versions(tmp_path: str, project_path) -> None:
    path_studies = Path(tmp_path)

    study = Mock()
    data = {"antares": {"caption": None}}
    study.get.return_value = data

    study_factory = Mock()
    study_factory.create_from_fs.return_value = (None, study)
    config = build_config(path_studies)
    study_service = RawStudyService(
        config=config,
        cache=Mock(),
        study_factory=study_factory,
        path_resources=project_path / "resources",
        patch_service=Mock(),
    )

    def create_study(version: int):
        metadata = RawStudy(
            id=f"study{version}",
            workspace=DEFAULT_WORKSPACE_NAME,
            path=str(get_default_workspace_path(config) / f"study{version}"),
            version=version,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )
        return study_service.create(metadata)

    md613 = create_study(613)
    md700 = create_study(700)
    md710 = create_study(710)
    md720 = create_study(720)
    md803 = create_study(803)

    path_study = path_studies / md613.id
    general_data_file = path_study / "settings" / "generaldata.ini"
    general_data = general_data_file.read_text()
    assert (
        re.search("^filtering = false", general_data, flags=re.MULTILINE)
        is not None
    )

    path_study = path_studies / md700.id
    general_data_file = path_study / "settings" / "generaldata.ini"
    general_data = general_data_file.read_text()
    assert (
        re.search("^link-type = local", general_data, flags=re.MULTILINE)
        is not None
    )
    assert (
        re.search(
            "^initial-reservoir-levels = cold start",
            general_data,
            flags=re.MULTILINE,
        )
        is not None
    )

    path_study = path_studies / md710.id
    general_data_file = path_study / "settings" / "generaldata.ini"
    general_data = general_data_file.read_text()
    assert (
        re.search(
            "^thematic-trimming = false", general_data, flags=re.MULTILINE
        )
        is not None
    )
    assert (
        re.search(
            "^geographic-trimming = false", general_data, flags=re.MULTILINE
        )
        is not None
    )

    path_study = path_studies / md720.id
    general_data_file = path_study / "settings" / "generaldata.ini"
    general_data = general_data_file.read_text()
    assert (
        re.search(
            "^include-unfeasible-problem-behavior = error-verbose",
            general_data,
            flags=re.MULTILINE,
        )
        is not None
    )

    path_study = path_studies / md803.id
    general_data_file = path_study / "settings" / "generaldata.ini"
    general_data = general_data_file.read_text()
    assert (
        re.search(
            "^custom-ts-numbers = false", general_data, flags=re.MULTILINE
        )
        is None
    )
    assert (
        re.search("^custom-scenario = false", general_data, flags=re.MULTILINE)
        is not None
    )
    assert (
        re.search(
            "^include-exportstructure = false",
            general_data,
            flags=re.MULTILINE,
        )
        is not None
    )
    assert (
        re.search(
            "^hydro-heuristic-policy = accommodate rule curves",
            general_data,
            flags=re.MULTILINE,
        )
        is not None
    )


@pytest.mark.unit_test
def test_copy_study(
    tmp_path: str,
    clean_ini_writer: Callable,
) -> None:
    path_studies = Path(tmp_path)
    source_name = "study1"
    path_study = path_studies / source_name
    path_study.mkdir()
    path_study_info = path_study / "study.antares"
    path_study_info.touch()

    value = {
        "antares": {
            "caption": "ex1",
            "created": 1480683452,
            "lastsave": 1602678639,
            "author": "unknown",
        },
    }

    study = Mock()
    study.get.return_value = value
    study_factory = Mock()

    config = Mock()
    study_factory.create_from_fs.return_value = config, study
    study_factory.create_from_config.return_value = study

    url_engine = Mock()
    url_engine.resolve.return_value = None, None, None
    config = build_config(path_studies)
    study_service = RawStudyService(
        config=config,
        cache=Mock(),
        study_factory=study_factory,
        path_resources=Path(),
        patch_service=Mock(),
    )

    src_md = RawStudy(
        id=source_name, workspace=DEFAULT_WORKSPACE_NAME, path=str(path_study)
    )
    md = study_service.copy(src_md, "dest_name")
    md_id = md.id
    assert str(md.path) == f"{tmp_path}{os.sep}{md_id}"
    study.get.assert_called_once_with(["study"])


@pytest.mark.unit_test
def test_delete_study(tmp_path: Path) -> None:
    name = "my-study"
    study_path = tmp_path / name
    study_path.mkdir()
    (study_path / "study.antares").touch()

    cache = Mock()
    study_service = RawStudyService(
        config=build_config(tmp_path),
        cache=cache,
        study_factory=Mock(),
        path_resources=Path(),
        patch_service=Mock(),
    )

    md = RawStudy(
        id=name, workspace=DEFAULT_WORKSPACE_NAME, path=str(study_path)
    )
    study_service.delete(md)
    cache.invalidate_all.assert_called_once_with(
        [
            f"{name}/{CacheConstants.RAW_STUDY}",
            f"{name}/{CacheConstants.STUDY_FACTORY}",
        ]
    )
    assert not study_path.exists()


@pytest.mark.unit_test
def test_edit_study(tmp_path: Path) -> None:
    # Mock
    (tmp_path / "my-uuid").mkdir()
    (tmp_path / "my-uuid/study.antares").touch()

    study = Mock()
    study_factory = Mock()
    study_factory.create_from_fs.return_value = None, study

    cache = Mock()
    study_service = RawStudyService(
        config=build_config(tmp_path),
        cache=cache,
        study_factory=study_factory,
        path_resources=Path(),
        patch_service=Mock(),
    )

    # Input
    url = "url/to/change"
    new = {"Hello": "World"}

    id = "my-uuid"
    md = RawStudy(
        id=id,
        workspace=DEFAULT_WORKSPACE_NAME,
        path=str(tmp_path / "my-uuid"),
    )
    res = study_service.edit_study(md, url, new)
    cache.invalidate_all.assert_called_once_with(
        [
            f"{id}/{CacheConstants.RAW_STUDY}",
            f"{id}/{CacheConstants.STUDY_FACTORY}",
        ]
    )
    assert new == res
    study.save.assert_called_once_with(new, ["url", "to", "change"])
