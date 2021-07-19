import os
import shutil
from pathlib import Path
import io
from unittest.mock import Mock

import pytest

from antarest.core.config import Config
from antarest.study.storage.rawstudy.importer_service import (
    ImporterService,
    fix_study_root,
)
from antarest.study.storage.rawstudy.raw_study_service import (
    RawStudyService,
)
from antarest.study.model import Study, DEFAULT_WORKSPACE_NAME, RawStudy
from antarest.core.exceptions import (
    IncorrectPathError,
    BadZipBinary,
    StudyValidationError,
)


def build_storage_service(workspace: Path, uuid: str) -> RawStudyService:
    service = Mock()
    service.get_workspace_path.return_value = workspace
    service.get_study_path.return_value = workspace / uuid
    return service


@pytest.mark.unit_test
def test_import_study(tmp_path: Path, storage_service_builder) -> None:

    name = "my-study"
    study_path = tmp_path / name
    study_path.mkdir()
    (study_path / "study.antares").touch()

    data = {"study": {"antares": {"version": 700}}}

    study = Mock()
    study.get.return_value = data
    study_factory = Mock()
    study_factory.create_from_fs.return_value = None, study

    study_service = Mock()
    study_service.get.return_value = data
    study_service.get_study_path.return_value = tmp_path / "other-study"

    importer_service = ImporterService(
        study_service=study_service,
        study_factory=study_factory,
    )

    filepath_zip = shutil.make_archive(
        str(study_path.absolute()), "zip", study_path
    )
    shutil.rmtree(study_path)

    path_zip = Path(filepath_zip)

    md = RawStudy(id="other-study", workspace=DEFAULT_WORKSPACE_NAME)
    with path_zip.open("rb") as input_file:
        md = importer_service.import_study(md, input_file)
        assert md.path == f"{tmp_path}{os.sep}other-study"

    shutil.rmtree(tmp_path / "other-study")
    with pytest.raises(BadZipBinary):
        importer_service.import_study(md, io.BytesIO(b""))


@pytest.mark.unit_test
def test_fix_root(tmp_path: Path):
    name = "my-study"
    study_path = tmp_path / name
    study_nested_root = study_path / "nested" / "real_root"
    os.makedirs(study_nested_root)
    (study_nested_root / "antares.study").touch()
    # when the study path is a single file
    with pytest.raises(StudyValidationError):
        fix_study_root(study_nested_root / "antares.study")

    shutil.rmtree(study_path)
    study_path = tmp_path / name
    study_nested_root = study_path / "nested" / "real_root"
    os.makedirs(study_nested_root)
    (study_nested_root / "antares.study").touch()
    os.mkdir(study_nested_root / "input")

    fix_study_root(study_path)
    study_files = os.listdir(study_path)
    assert len(study_files) == 2
    assert "antares.study" in study_files and "input" in study_files

    shutil.rmtree(study_path)
