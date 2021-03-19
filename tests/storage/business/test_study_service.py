from pathlib import Path
from typing import Callable
from unittest.mock import Mock

import pytest

from antarest.common.config import Config
from antarest.common.requests import (
    RequestParameters,
)
from antarest.storage.business.study_service import StudyService
from antarest.storage.model import Metadata
from antarest.storage.web.exceptions import (
    StudyNotFoundError,
)


def build_config(study_path: Path):
    return Config(
        {
            "storage": {
                "workspaces": {"default": {"path": str(study_path.absolute())}}
            }
        }
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

    study_service = StudyService(
        config=build_config(path_to_studies),
        study_factory=study_factory,
        path_resources=project_path / "resources",
    )

    metadata = Metadata(id="study2.py", workspace="default")
    output = study_service.get(metadata=metadata, url=sub_route, depth=2)

    assert output == data

    study.get.assert_called_once_with(["settings"], depth=2)


@pytest.mark.unit_test
def test_check_errors():
    study = Mock()
    study.check_errors.return_value = ["Hello"]

    factory = Mock()
    factory.create_from_fs.return_value = None, study

    study_service = StudyService(
        config=build_config(Path()),
        study_factory=factory,
        path_resources=Path(),
    )

    metadata = Metadata(id="study", workspace="default")
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
    study_service = StudyService(
        config=build_config(path_to_studies),
        study_factory=Mock(),
        path_resources=project_path / "resources",
    )

    metadata = Metadata(id=study_name, workspace="default")
    study_service.check_study_exists(metadata)


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
    study_service = StudyService(
        config=build_config(path_to_studies),
        study_factory=Mock(),
        path_resources=project_path / "resources",
    )

    metadata = Metadata(id=study_name, workspace="default")
    with pytest.raises(StudyNotFoundError):
        study_service.check_study_exists(metadata)


@pytest.mark.unit_test
def test_find_studies(tmp_path: str, storage_service_builder) -> None:
    # Create folders
    path_studies = Path(tmp_path) / "studies"
    path_studies.mkdir()

    path_study1 = path_studies / "study1"
    path_study1.mkdir()
    (path_study1 / "study.antares").touch()

    path_study2 = path_studies / "study2"
    path_study2.mkdir()
    (path_study2 / "study.antares").touch()

    path_not_study = path_studies / "not_a_study"
    path_not_study.mkdir()
    (path_not_study / "lambda.txt").touch()

    path_lambda = path_studies / "folder1"
    path_lambda.mkdir()
    path_study_misplaced = path_lambda / "study_misplaced"
    path_study_misplaced.mkdir()
    (path_study_misplaced / "study.antares").touch()
    # Input
    study_names = ["study1", "study2"]

    # Test & Verify
    study_service = StudyService(
        config=build_config(path_studies),
        study_factory=Mock(),
        path_resources=Path(),
    )

    assert study_names == study_service.get_study_uuids()


@pytest.mark.unit_test
def test_create_study(
    tmp_path: str, storage_service_builder, project_path
) -> None:

    path_studies = Path(tmp_path)

    study = Mock()
    data = {"study": {"antares": {"caption": None}}}
    study.get.return_value = data

    study_factory = Mock()
    study_factory.create_from_fs.return_value = (None, study)

    study_service = StudyService(
        config=build_config(path_studies),
        study_factory=study_factory,
        path_resources=project_path / "resources",
    )

    metadata = Metadata(id="study1", workspace="default")
    md = study_service.create_study(metadata)

    assert md.path == f"{tmp_path}/study1"
    path_study = path_studies / md.id
    assert path_study.exists()

    path_study_antares_infos = path_study / "study.antares"
    assert path_study_antares_infos.is_file()


@pytest.mark.unit_test
def test_copy_study(
    tmp_path: str,
    clean_ini_writer: Callable,
    storage_service_builder,
) -> None:

    path_studies = Path(tmp_path)
    source_name = "study1"
    path_study = path_studies / source_name
    path_study.mkdir()
    path_study_info = path_study / "study.antares"
    path_study_info.touch()

    value = {
        "study": {
            "antares": {
                "caption": "ex1",
                "created": 1480683452,
                "lastsave": 1602678639,
                "author": "unknown",
            },
            "output": [],
        }
    }

    study = Mock()
    study.get.return_value = value
    study_factory = Mock()

    config = Mock()
    study_factory.create_from_fs.return_value = config, study
    study_factory.create_from_config.return_value = study

    url_engine = Mock()
    url_engine.resolve.return_value = None, None, None

    study_service = StudyService(
        config=build_config(path_studies),
        study_factory=study_factory,
        path_resources=Path(),
    )

    src_md = Metadata(id=source_name, workspace="default")
    dest_md = Metadata(id="study2", workspace="default")
    md = study_service.copy_study(src_md, dest_md)

    assert md == f"{tmp_path}/study2"
    study.get.assert_called_once_with()


@pytest.mark.unit_test
def test_delete_study(tmp_path: Path, storage_service_builder) -> None:

    name = "my-study"
    study_path = tmp_path / name
    study_path.mkdir()
    (study_path / "study.antares").touch()

    study_service = StudyService(
        config=build_config(tmp_path),
        study_factory=Mock(),
        path_resources=Path(),
    )

    md = Metadata(id=name, workspace="default")
    study_service.delete_study(md)

    assert not study_path.exists()


@pytest.mark.unit_test
def test_edit_study(tmp_path: Path, storage_service_builder) -> None:
    # Mock
    (tmp_path / "my-uuid").mkdir()
    (tmp_path / "my-uuid/study.antares").touch()

    study = Mock()
    study_factory = Mock()
    study_factory.create_from_fs.return_value = None, study

    study_service = StudyService(
        config=build_config(tmp_path),
        study_factory=study_factory,
        path_resources=Path(),
    )

    # Input
    url = "url/to/change"
    new = {"Hello": "World"}

    md = Metadata(id="my-uuid", workspace="default")
    res = study_service.edit_study(md, url, new)

    assert new == res
    study.save.assert_called_once_with(new, ["url", "to", "change"])
