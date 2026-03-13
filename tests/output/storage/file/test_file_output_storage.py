# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.
import os
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

import pytest
from typing_extensions import override

from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.exceptions import (
    OutputAlreadyArchived,
    OutputAlreadyExists,
    OutputAlreadyUnarchived,
    OutputNotFound,
    StudyNotFoundError,
)
from antarest.core.remote.remote_executor import IRemoteExecutor
from antarest.core.utils.archives import ArchiveFormat, archive_dir
from antarest.launcher.adapters.abstractlauncher import SimulationLogs
from antarest.launcher.model import LogType
from antarest.matrixstore.in_memory import InMemorySimpleMatrixService
from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapperFactory, NormalizedMatrixUriMapper
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.output.storage.file.storage import (
    FileStudyOutputs,
    IFileOutputsProvider,
    InStudyFileOutputStorage,
)
from antarest.output.storage.output_storage import OutputDetails, OutputMetadata, OutputStorageType
from antarest.study.storage.rawstudy.model.filesystem.config.files import build
from antarest.study.storage.rawstudy.model.filesystem.config.model import Mode
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree


@pytest.fixture
def sta_mini_zip_path(project_path: Path) -> Path:
    return project_path / "examples/studies/STA-mini.zip"


class SimpleFileOutputsProvider(IFileOutputsProvider):
    """
    Maps study ID to outputs in <studies_dir> / <study_id> / output
    """

    def __init__(self, studies_dir: Path, matrix_service: ISimpleMatrixService):
        self._studies_dir = studies_dir
        self._matrix_service = matrix_service

    @override
    def get_outputs(self, study_id: str) -> FileStudyOutputs:
        if not (self._studies_dir / study_id).is_dir():
            raise StudyNotFoundError(f"Studies directory {self._studies_dir} not found.")
        return FileStudyOutputs(
            get_file_study=lambda: self._get_study(study_id),
            outputs_path=self._studies_dir / study_id / "output",
            study_workspace="default",
        )

    def _get_study(self, study_id: str) -> FileStudy:
        study_dir = self._studies_dir / study_id
        if not study_dir.is_dir():
            raise StudyNotFoundError(f"Study {study_id} not found.")
        config = build(study_dir, study_id)
        mapper_factory = MatrixUriMapperFactory(matrix_service=self._matrix_service)
        matrix_mapper = mapper_factory.create(NormalizedMatrixUriMapper.NORMALIZED)
        return FileStudy(config, FileStudyTree(matrix_mapper, config))


@pytest.fixture
def matrix_service() -> ISimpleMatrixService:
    return InMemorySimpleMatrixService()


@pytest.fixture
def file_output_storage(
    tmp_path: Path, sta_mini_zip_path: Path, matrix_service: ISimpleMatrixService
) -> InStudyFileOutputStorage:
    executor = Mock(spec=IRemoteExecutor)

    studies_dir = tmp_path / "studies"
    studies_dir.mkdir()

    with zipfile.ZipFile(sta_mini_zip_path, "r") as zf:
        # outputs_filter = [
        #     n
        #     for n in zf.namelist()
        #     if n.startswith(
        #         "STA-mini/output/20201014-1427eco" or n.startswith("STA-mini/output/20201014-1422eco-hello")
        #     )
        # ]
        # zf.extractall(studies_dir, members=outputs_filter)
        zf.extractall(studies_dir)

    outputs_provider = SimpleFileOutputsProvider(studies_dir, matrix_service)

    return InStudyFileOutputStorage(
        outputs_provider=outputs_provider, cache=LocalCache(), remote_executor=executor, repository=Mock()
    )


def test_file_output_storage(file_output_storage):
    assert file_output_storage.list_outputs("STA-mini") == [
        OutputMetadata(id="20201014-1422eco-hello", in_study=True, archived=False),
        OutputMetadata(id="20201014-1425eco-goodbye", in_study=True, archived=False),
        OutputMetadata(id="20201014-1427eco", in_study=True, archived=False),
        OutputMetadata(id="20201014-1430adq", in_study=True, archived=False),
        OutputMetadata(id="20201014-1430adq-2", in_study=True, archived=True),
        OutputMetadata(id="20241807-1540eco-extra-outputs", in_study=True, archived=False),
    ]

    with pytest.raises(StudyNotFoundError):
        file_output_storage.list_outputs("non-existent")

    assert [
        file_output_storage.get_output_details("STA-mini", o.id) for o in file_output_storage.list_outputs("STA-mini")
    ] == [
        OutputDetails(
            name="20201014-1422eco-hello",
            mode=Mode.ECONOMY,
            synthesis=True,
            by_year=True,
            nb_years=1,
            archived=False,
            storage_type=OutputStorageType.IN_STUDY_FILE_TREE,
        ),
        OutputDetails(
            name="20201014-1425eco-goodbye",
            mode=Mode.ECONOMY,
            synthesis=True,
            by_year=True,
            nb_years=2,
            archived=False,
            storage_type=OutputStorageType.IN_STUDY_FILE_TREE,
        ),
        OutputDetails(
            name="20201014-1427eco",
            mode=Mode.ECONOMY,
            synthesis=True,
            by_year=False,
            nb_years=1,
            archived=False,
            storage_type=OutputStorageType.IN_STUDY_FILE_TREE,
        ),
        OutputDetails(
            name="20201014-1430adq",
            mode=Mode.ADEQUACY,
            synthesis=True,
            by_year=False,
            nb_years=1,
            archived=False,
            storage_type=OutputStorageType.IN_STUDY_FILE_TREE,
        ),
        OutputDetails(
            name="20201014-1430adq-2",
            mode=Mode.ADEQUACY,
            synthesis=True,
            by_year=False,
            nb_years=1,
            archived=True,
            storage_type=OutputStorageType.IN_STUDY_FILE_TREE,
        ),
        OutputDetails(
            name="20241807-1540eco-extra-outputs",
            mode=Mode.ECONOMY,
            synthesis=True,
            by_year=True,
            nb_years=1,
            archived=False,
            storage_type=OutputStorageType.IN_STUDY_FILE_TREE,
        ),
    ]

    with pytest.raises(StudyNotFoundError):
        file_output_storage.get_output_details("unknown", "20241807-1540eco-extra-outputs")

    with pytest.raises(OutputNotFound):
        file_output_storage.get_output_details("STA-mini", "absent")


def test_output_deletion(file_output_storage: InStudyFileOutputStorage) -> None:
    outputs = file_output_storage.list_outputs("STA-mini")
    assert len(outputs) == 6
    assert "20201014-1427eco" in [o.id for o in outputs]
    file_output_storage.delete_output("STA-mini", "20201014-1427eco")

    outputs = file_output_storage.list_outputs("STA-mini")
    assert len(outputs) == 5
    assert "20201014-1427eco" not in [o.id for o in outputs]

    # TODO: could add a check on the directory on disk
    with pytest.raises(StudyNotFoundError):
        file_output_storage.delete_output("non-existent", "20201014-1427eco")

    with pytest.raises(OutputNotFound):
        file_output_storage.delete_output("STA-mini", "non-existent")

    file_output_storage.archive_study_output("STA-mini", "20201014-1422eco-hello")
    assert file_output_storage.is_output_archived("STA-mini", "20201014-1422eco-hello")
    assert "20201014-1422eco-hello" in [o.id for o in outputs]

    file_output_storage.delete_output("STA-mini", "20201014-1422eco-hello")
    outputs = file_output_storage.list_outputs("STA-mini")
    assert len(outputs) == 4
    assert "20201014-1422eco-hello" not in [o.id for o in outputs]


def test_output_archival(file_output_storage) -> None:
    assert not file_output_storage.is_output_archived("STA-mini", "20201014-1422eco-hello")
    file_output_storage.archive_study_output("STA-mini", "20201014-1422eco-hello")
    assert file_output_storage.is_output_archived("STA-mini", "20201014-1422eco-hello")

    outputs = file_output_storage.list_outputs("STA-mini")
    assert "20201014-1422eco-hello" in [o.id for o in outputs if o.archived]

    with pytest.raises(OutputAlreadyArchived):
        file_output_storage.archive_study_output("STA-mini", "20201014-1422eco-hello")

    # TODO: check zipped on disk

    file_output_storage.unarchive_study_output("STA-mini", "20201014-1422eco-hello")
    assert not file_output_storage.is_output_archived("STA-mini", "20201014-1422eco-hello")

    outputs = file_output_storage.list_outputs("STA-mini")
    assert "20201014-1422eco-hello" in [o.id for o in outputs if not o.archived]

    with pytest.raises(OutputAlreadyUnarchived):
        file_output_storage.unarchive_study_output("STA-mini", "20201014-1422eco-hello")

    with pytest.raises(StudyNotFoundError):
        file_output_storage.archive_study_output("non-existent", "non-existent")
    with pytest.raises(OutputNotFound):
        file_output_storage.archive_study_output("STA-mini", "non-existent")

    with pytest.raises(StudyNotFoundError):
        file_output_storage.unarchive_study_output("non-existent", "non-existent")
    with pytest.raises(OutputNotFound):
        file_output_storage.unarchive_study_output("STA-mini", "non-existent")


def test_output_copy(file_output_storage: InStudyFileOutputStorage, tmp_path: Path) -> None:
    # Create a copy of the STA-mini study without outputs
    studies_dir = tmp_path / "studies"
    sta_mini_path = studies_dir / "STA-mini"
    copy_path = studies_dir / "STA-mini-copy"
    shutil.copytree(sta_mini_path, copy_path, ignore=shutil.ignore_patterns("output"))
    (copy_path / "output").mkdir()

    assert file_output_storage.list_outputs("STA-mini-copy") == []

    file_output_storage.copy_output("STA-mini", "STA-mini-copy", "20201014-1422eco-hello")
    outputs = file_output_storage.list_outputs("STA-mini-copy")
    assert [o.id for o in outputs] == ["20201014-1422eco-hello"]

    # Copy an archived output
    file_output_storage.archive_study_output("STA-mini", "20201014-1427eco")
    assert file_output_storage.is_output_archived("STA-mini", "20201014-1427eco")
    file_output_storage.copy_output("STA-mini", "STA-mini-copy", "20201014-1427eco")
    outputs = file_output_storage.list_outputs("STA-mini-copy")
    assert [o.id for o in outputs] == ["20201014-1422eco-hello", "20201014-1427eco"]
    assert file_output_storage.is_output_archived("STA-mini-copy", "20201014-1427eco")

    with pytest.raises(StudyNotFoundError):
        file_output_storage.copy_output("non-existent", "STA-mini-copy", "20201014-1427eco")
    with pytest.raises(StudyNotFoundError):
        file_output_storage.copy_output("STA-mini", "non-existent", "20201014-1427eco")
    with pytest.raises(OutputNotFound):
        file_output_storage.copy_output("STA-mini", "STA-mini-copy", "non-existent")

    with pytest.raises(OutputAlreadyExists):
        file_output_storage.copy_output("STA-mini", "STA-mini-copy", "20201014-1427eco")
    with pytest.raises(OutputAlreadyExists):
        file_output_storage.copy_output("STA-mini", "STA-mini-copy", "20201014-1422eco-hello")


def test_output_exists(file_output_storage: InStudyFileOutputStorage) -> None:
    assert file_output_storage.output_exists("STA-mini", "20201014-1427eco")
    assert not file_output_storage.output_exists("STA-mini", "non-existent")

    file_output_storage.archive_study_output("STA-mini", "20201014-1427eco")
    assert file_output_storage.is_output_archived("STA-mini", "20201014-1427eco")
    assert file_output_storage.output_exists("STA-mini", "20201014-1427eco")

    with pytest.raises(StudyNotFoundError):
        file_output_storage.output_exists("non-existent", "20201014-1427eco")


def _count_files_in_dir(dir_path: Path) -> int:
    return sum(len(d[2]) for d in os.walk(dir_path))


def _count_files_in_zip(zip_path: Path) -> int:
    with zipfile.ZipFile(zip_path, "r") as zf:
        return len(zf.namelist())


def test_export_output(file_output_storage: InStudyFileOutputStorage, tmp_path: Path) -> None:
    # We are just checking the count of files is correct as a proxy of a full content check
    expected_count = 79

    zip_path = tmp_path / "output.zip"
    file_output_storage.export_output("STA-mini", "20201014-1427eco", zip_path)
    assert zip_path.exists()
    assert _count_files_in_zip(zip_path) == expected_count

    # Check on archived study
    file_output_storage.archive_study_output("STA-mini", "20201014-1427eco")
    zip_path = tmp_path / "output2.zip"
    file_output_storage.export_output("STA-mini", "20201014-1427eco", zip_path)
    assert zip_path.exists()
    assert _count_files_in_zip(zip_path) == expected_count

    with pytest.raises(StudyNotFoundError):
        file_output_storage.export_output("non-existent", "20201014-1427eco", zip_path)
    with pytest.raises(OutputNotFound):
        file_output_storage.export_output("STA-mini", "non-existent", zip_path)


def test_write_output_to_dir(file_output_storage: InStudyFileOutputStorage, tmp_path: Path) -> None:
    # We just checking the count of files is correct as a proxy of a full content check
    expected_count = 79

    export_path = tmp_path / "export"
    export_path.mkdir()
    file_output_storage.write_output_to_dir("STA-mini", "20201014-1427eco", export_path)
    expected_path = export_path / "20201014-1427eco"
    assert expected_path.is_dir()
    assert "about-the-study" in os.listdir(expected_path)
    assert _count_files_in_dir(expected_path) == expected_count

    # Check on archived study
    file_output_storage.archive_study_output("STA-mini", "20201014-1427eco")
    export_path = tmp_path / "export2"
    export_path.mkdir()
    file_output_storage.write_output_to_dir("STA-mini", "20201014-1427eco", export_path)
    expected_path = export_path / "20201014-1427eco"
    assert expected_path.is_dir()
    assert "about-the-study" in os.listdir(expected_path)
    assert _count_files_in_dir(expected_path) == expected_count

    with pytest.raises(StudyNotFoundError):
        file_output_storage.write_output_to_dir("non-existent", "20201014-1427eco", export_path)
    with pytest.raises(OutputNotFound):
        file_output_storage.write_output_to_dir("STA-mini", "non-existent", export_path)


def test_get_logs(file_output_storage: InStudyFileOutputStorage, tmp_path: Path) -> None:
    # Will write fake logs to underlying output dir
    outputs_path = tmp_path / "studies" / "STA-mini" / "output"

    (outputs_path / "logs").mkdir()

    possible_log_paths = [
        outputs_path / "20201014-1427eco" / "antares-out.log",
        outputs_path / "20201014-1427eco" / "simulation.log",
    ]

    for log_path in possible_log_paths:
        log_path.write_text("some log 2")
        logs = file_output_storage.get_logs("STA-mini", "20201014-1427eco", LogType.STDOUT)
        assert logs == "some log 2"
        log_path.unlink()

        # Check invalid utf-8 characters are correctly replaced
        log_path.write_text("Caractère invalide", encoding="latin-1")
        logs = file_output_storage.get_logs("STA-mini", "20201014-1427eco", LogType.STDOUT)
        assert logs == "Caract�re invalide"
        log_path.unlink()


def _extract_output_to_dir(study_zip: Path, output_path: str, target_dir: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        with zipfile.ZipFile(study_zip, "r") as zf:
            names = [n for n in zf.namelist() if n.startswith(output_path)]
            zf.extractall(tmp_dir, members=names)
        (tmp_dir / "STA-mini" / "output" / "20201014-1422eco-hello").rename(target_dir)


def _utc_to_local_date(date_str: str) -> str:
    """Converts a UTC date string such as "20201014-1222" to a local date string such as "20201014-1422"."""
    utc_date = datetime.strptime(date_str, "%Y%m%d-%H%M").replace(tzinfo=timezone.utc)
    return utc_date.astimezone().strftime("%Y%m%d-%H%M")


def test_import_output_directory(
    file_output_storage: InStudyFileOutputStorage, tmp_path: Path, sta_mini_zip_path: Path
) -> None:
    # Extract one of the outputs of STA-mini to a directory
    studies_dir = tmp_path / "studies"

    study_dir = studies_dir / "my-study"
    study_dir.mkdir()

    output_dir = tmp_path / "import-output"
    _extract_output_to_dir(sta_mini_zip_path, "STA-mini/output/20201014-1422eco-hello", output_dir)

    # Import directory
    file_output_storage.import_output("my-study", output_dir)

    # Cannot hard code the expected formatted date because it depends on the locale
    expected_date = _utc_to_local_date("20201014-1222")

    expected_output_dir = study_dir / "output" / f"{expected_date}eco-hello"
    assert expected_output_dir.exists()
    assert file_output_storage.list_outputs("my-study") == [
        OutputMetadata(id=f"{expected_date}eco-hello", in_study=True, archived=False)
    ]

    # Import directory with logs and suffix
    out_logs = tmp_path / "out.log"
    out_logs.write_text("some log")
    err_logs = tmp_path / "err.log"
    err_logs.write_text("some error")
    file_output_storage.import_output(
        "my-study", output_dir, output_name_suffix="other", logs=SimulationLogs(out_logs, err_logs)
    )
    assert file_output_storage.list_outputs("my-study") == [
        OutputMetadata(id=f"{expected_date}eco-hello", in_study=True, archived=False),
        OutputMetadata(id=f"{expected_date}eco-other", in_study=True, archived=False),
    ]

    assert file_output_storage.get_logs("my-study", f"{expected_date}eco-other", LogType.STDOUT) == "some log"
    assert file_output_storage.get_logs("my-study", f"{expected_date}eco-other", LogType.STDERR) == "some error"


def test_import_output_zip_should_import_it_as_archived(
    file_output_storage: InStudyFileOutputStorage, tmp_path: Path, sta_mini_zip_path: Path
) -> None:
    # Checks the "optimized path" for zipped outputs, see TODOs

    # Extract one of the outputs of STA-mini to a directory and zip it
    studies_dir = tmp_path / "studies"

    study_dir = studies_dir / "my-study"
    study_dir.mkdir()

    zip_path = tmp_path / "import-output.zip"
    output_dir = tmp_path / "import-output"
    _extract_output_to_dir(sta_mini_zip_path, "STA-mini/output/20201014-1422eco-hello", output_dir)
    archive_dir(src_dir_path=output_dir, target_archive_path=zip_path, remove_source_dir=True)

    # Import zip file
    output_id = file_output_storage.import_output("my-study", zip_path)

    # Cannot hard code the expected formatted date because it depends on the locale
    expected_date = _utc_to_local_date("20201014-1222")

    assert output_id == f"{expected_date}eco-hello"
    assert file_output_storage.list_outputs("my-study") == [
        OutputMetadata(id=f"{expected_date}eco-hello", in_study=True, archived=True)
    ]

    # Import zip file with logs and suffix
    out_logs = tmp_path / "out.log"
    out_logs.write_text("some log")
    err_logs = tmp_path / "err.log"
    err_logs.write_text("some error")
    output_id = file_output_storage.import_output(
        "my-study", zip_path, output_name_suffix="other", logs=SimulationLogs(out_logs, err_logs)
    )
    assert output_id == f"{expected_date}eco-other"
    assert file_output_storage.list_outputs("my-study") == [
        OutputMetadata(id=f"{expected_date}eco-hello", in_study=True, archived=True),
        OutputMetadata(id=f"{expected_date}eco-other", in_study=True, archived=True),
    ]

    file_output_storage.unarchive_study_output("my-study", f"{expected_date}eco-other")

    assert file_output_storage.get_logs("my-study", f"{expected_date}eco-other", LogType.STDOUT) == "some log"
    assert file_output_storage.get_logs("my-study", f"{expected_date}eco-other", LogType.STDERR) == "some error"


@pytest.mark.parametrize("archive_format", [ArchiveFormat.ZIP, ArchiveFormat.SEVEN_ZIP])
def test_import_output_archive_stream(
    file_output_storage: InStudyFileOutputStorage,
    tmp_path: Path,
    sta_mini_zip_path: Path,
    archive_format: ArchiveFormat,
) -> None:
    # Checks the "optimized path" for zipped outputs, see TODOs

    # Extract one of the outputs of STA-mini to a directory and zip it
    studies_dir = tmp_path / "studies"

    study_dir = studies_dir / "my-study"
    study_dir.mkdir()

    archive_path = tmp_path / f"import-output{archive_format}"
    output_dir = tmp_path / "import-output"
    _extract_output_to_dir(sta_mini_zip_path, "STA-mini/output/20201014-1422eco-hello", output_dir)
    archive_dir(
        src_dir_path=output_dir, target_archive_path=archive_path, remove_source_dir=True, archive_format=archive_format
    )

    # Import archive stream
    with open(archive_path, "rb") as f:
        file_output_storage.import_output("my-study", f)

    # Cannot hard code the expected formatted date because it depends on the locale
    expected_date = _utc_to_local_date("20201014-1222")

    assert file_output_storage.list_outputs("my-study") == [
        OutputMetadata(id=f"{expected_date}eco-hello", in_study=True, archived=False)
    ]
