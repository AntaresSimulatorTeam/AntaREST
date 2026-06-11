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
import zipfile
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
from antarest.output.storage.file.abstract_storage import FileStudyOutputs, IFileOutputsProvider
from antarest.output.storage.file.in_study import InStudyFileOutputStorage
from antarest.output.storage.file.outside_study import OutsideStudyFileOutputStorage
from antarest.output.storage.output_storage import (
    IOutputStorage,
    OutputDetails,
    OutputMetadata,
    OutputSettings,
    OutputSettingsGeneral,
    OutputSettingsOptimization,
    OutputStorageType,
)
from antarest.study.model import DEFAULT_WORKSPACE_NAME
from antarest.study.storage.rawstudy.model.filesystem.config.model import Mode
from tests.test_helpers.dates import utc_to_local


@pytest.fixture
def sta_mini_zip_path(project_path: Path) -> Path:
    return project_path / "examples/studies/STA-mini.zip"


class InStudySimpleFileOutputsProvider(IFileOutputsProvider):
    """
    Maps study ID to outputs in <studies_dir> / <study_id> / output
    """

    def __init__(self, studies_dir: Path):
        self._studies_dir = studies_dir

    @override
    def get_outputs(self, study_id: str) -> FileStudyOutputs:
        if not (self._studies_dir / study_id).is_dir():
            raise StudyNotFoundError(f"Studies directory {self._studies_dir} not found.")
        return FileStudyOutputs(
            outputs_path=self._studies_dir / study_id / "output", study_workspace=DEFAULT_WORKSPACE_NAME
        )


class OutsideStudyFileOutputProvider(IFileOutputsProvider):
    def __init__(self, outputs_dir: Path):
        self._outputs_dir = outputs_dir

    @override
    def get_outputs(self, study_id: str) -> FileStudyOutputs:
        if not (self._outputs_dir / study_id).is_dir():
            raise StudyNotFoundError(f"Studies directory {self._outputs_dir / study_id} not found.")
        return FileStudyOutputs(outputs_path=self._outputs_dir / study_id, study_workspace=DEFAULT_WORKSPACE_NAME)


@pytest.fixture(params=[OutputStorageType.IN_STUDY_FILE_TREE, OutputStorageType.OUTSIDE_STUDY_FILE_TREE])
def output_storage(request, tmp_path: Path, sta_mini_zip_path: Path) -> IOutputStorage:
    executor = Mock(spec=IRemoteExecutor)

    studies_dir = tmp_path / "studies"
    studies_dir.mkdir()

    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    with zipfile.ZipFile(sta_mini_zip_path, "r") as zf:
        zf.extractall(studies_dir)

    if request.param == OutputStorageType.IN_STUDY_FILE_TREE:
        klass = InStudyFileOutputStorage
        outputs_provider = InStudySimpleFileOutputsProvider(studies_dir)
    else:
        klass = OutsideStudyFileOutputStorage
        outputs_provider = OutsideStudyFileOutputProvider(outputs_dir)
        # Move the outputs and remove the study folder
        (studies_dir / "STA-mini" / "output").rename(outputs_dir / "STA-mini")
        shutil.rmtree(studies_dir)

    return klass(outputs_provider=outputs_provider, cache=LocalCache(), remote_executor=executor, repository=Mock())


def test_file_output_storage(output_storage: IOutputStorage) -> None:
    storage_type = output_storage.storage_type
    in_study = storage_type == OutputStorageType.IN_STUDY_FILE_TREE

    assert output_storage.list_outputs("STA-mini") == [
        OutputMetadata(id="20201014-1422eco-hello", in_study=in_study, archived=False),
        OutputMetadata(id="20201014-1425eco-goodbye", in_study=in_study, archived=False),
        OutputMetadata(id="20201014-1427eco", in_study=in_study, archived=False),
        OutputMetadata(id="20201014-1430adq", in_study=in_study, archived=False),
        OutputMetadata(id="20201014-1430adq-2", in_study=in_study, archived=True),
        OutputMetadata(id="20241807-1540eco-extra-outputs", in_study=in_study, archived=False),
    ]

    with pytest.raises(StudyNotFoundError):
        output_storage.list_outputs("non-existent")

    assert output_storage.get_output_details("STA-mini") == [
        OutputDetails(
            name="20201014-1422eco-hello",
            mode=Mode.ECONOMY,
            synthesis=True,
            by_year=True,
            nb_years=1,
            archived=False,
            storage_type=storage_type,
            settings=OutputSettings(
                general=OutputSettingsGeneral(
                    mode="Economy",
                    horizon="2030",
                    nbyears=1,
                    simulation_start=1,
                    simulation_end=7,
                    january_1st="Monday",
                    first_month_in_year="january",
                    first_weekday="Monday",
                    leapyear=False,
                    year_by_year=True,
                    user_playlist=True,
                ),
                optimization=OutputSettingsOptimization(transmission_capacities=True),
                playlist=[1],
            ),
        ),
        OutputDetails(
            name="20201014-1425eco-goodbye",
            mode=Mode.ECONOMY,
            synthesis=True,
            by_year=True,
            nb_years=2,
            archived=False,
            storage_type=storage_type,
            settings=OutputSettings(
                general=OutputSettingsGeneral(
                    mode="Economy",
                    horizon="2030",
                    nbyears=2,
                    simulation_start=1,
                    simulation_end=14,
                    january_1st="Monday",
                    first_month_in_year="january",
                    first_weekday="Monday",
                    leapyear=False,
                    year_by_year=True,
                    user_playlist=True,
                ),
                optimization=OutputSettingsOptimization(transmission_capacities=True),
                playlist=[1],
            ),
        ),
        OutputDetails(
            name="20201014-1427eco",
            mode=Mode.ECONOMY,
            synthesis=True,
            by_year=False,
            nb_years=1,
            archived=False,
            storage_type=storage_type,
            settings=OutputSettings(
                general=OutputSettingsGeneral(
                    mode="Economy",
                    horizon="2030",
                    nbyears=1,
                    simulation_start=1,
                    simulation_end=7,
                    january_1st="Monday",
                    first_month_in_year="january",
                    first_weekday="Monday",
                    leapyear=False,
                    year_by_year=False,
                    user_playlist=True,
                ),
                optimization=OutputSettingsOptimization(transmission_capacities=True),
                playlist=[1],
            ),
        ),
        OutputDetails(
            name="20201014-1430adq",
            mode=Mode.ADEQUACY,
            synthesis=True,
            by_year=False,
            nb_years=1,
            archived=False,
            storage_type=storage_type,
            settings=OutputSettings(
                general=OutputSettingsGeneral(
                    mode="Adequacy",
                    horizon="2030",
                    nbyears=1,
                    simulation_start=1,
                    simulation_end=7,
                    january_1st="Monday",
                    first_month_in_year="january",
                    first_weekday="Monday",
                    leapyear=False,
                    year_by_year=False,
                    user_playlist=True,
                ),
                optimization=OutputSettingsOptimization(transmission_capacities=True),
                playlist=[1],
            ),
        ),
        OutputDetails(
            name="20201014-1430adq-2",
            mode=Mode.ADEQUACY,
            synthesis=True,
            by_year=False,
            nb_years=1,
            archived=True,
            storage_type=storage_type,
            settings=OutputSettings(
                general=OutputSettingsGeneral(
                    mode="Adequacy",
                    horizon="2030",
                    nbyears=1,
                    simulation_start=1,
                    simulation_end=7,
                    january_1st="Monday",
                    first_month_in_year="january",
                    first_weekday="Monday",
                    leapyear=False,
                    year_by_year=False,
                    user_playlist=True,
                ),
                optimization=OutputSettingsOptimization(transmission_capacities=True),
                playlist=[1],
            ),
        ),
        OutputDetails(
            name="20241807-1540eco-extra-outputs",
            mode=Mode.ECONOMY,
            synthesis=True,
            by_year=True,
            nb_years=1,
            archived=False,
            storage_type=storage_type,
            settings=OutputSettings(
                general=OutputSettingsGeneral(
                    mode="Economy",
                    horizon="",
                    nbyears=1,
                    simulation_start=1,
                    simulation_end=365,
                    january_1st="Monday",
                    first_month_in_year="january",
                    first_weekday="Monday",
                    leapyear=False,
                    year_by_year=True,
                    user_playlist=False,
                ),
                optimization=OutputSettingsOptimization(transmission_capacities="local-values"),
                playlist=[],
            ),
        ),
    ]

    with pytest.raises(StudyNotFoundError):
        output_storage.get_output_details("unknown")


def test_output_deletion(output_storage: IOutputStorage, tmp_path: Path) -> None:
    outputs = output_storage.list_outputs("STA-mini")
    assert len(outputs) == 6
    assert "20201014-1427eco" in [o.id for o in outputs]
    output_storage.delete_output("STA-mini", "20201014-1427eco")

    outputs = output_storage.list_outputs("STA-mini")
    assert len(outputs) == 5
    assert "20201014-1427eco" not in [o.id for o in outputs]

    # Check that the output is deleted from the disk
    if output_storage.storage_type == OutputStorageType.IN_STUDY_FILE_TREE:
        assert not (tmp_path / "studies" / "STA-mini" / "output" / "20201014-1427eco").exists()
    else:
        assert not (tmp_path / "outputs" / "STA-mini" / "20201014-1427eco").exists()

    with pytest.raises(StudyNotFoundError):
        output_storage.delete_output("non-existent", "20201014-1427eco")

    with pytest.raises(OutputNotFound):
        output_storage.delete_output("STA-mini", "non-existent")

    output_storage.archive_study_output("STA-mini", "20201014-1422eco-hello")
    assert output_storage.is_output_archived("STA-mini", "20201014-1422eco-hello")
    assert "20201014-1422eco-hello" in [o.id for o in outputs]

    output_storage.delete_output("STA-mini", "20201014-1422eco-hello")
    outputs = output_storage.list_outputs("STA-mini")
    assert len(outputs) == 4
    assert "20201014-1422eco-hello" not in [o.id for o in outputs]


def test_output_archival(output_storage: IOutputStorage, tmp_path: Path) -> None:
    assert not output_storage.is_output_archived("STA-mini", "20201014-1422eco-hello")
    output_storage.archive_study_output("STA-mini", "20201014-1422eco-hello")
    assert output_storage.is_output_archived("STA-mini", "20201014-1422eco-hello")

    # Check that the output is archived on the disk
    if output_storage.storage_type == OutputStorageType.IN_STUDY_FILE_TREE:
        output_folder = tmp_path / "studies" / "STA-mini" / "output"
    else:
        output_folder = tmp_path / "outputs" / "STA-mini"
    assert not (output_folder / "20201014-1422eco-hello").exists()
    assert (output_folder / "20201014-1422eco-hello.zip").exists()

    outputs = output_storage.list_outputs("STA-mini")
    assert "20201014-1422eco-hello" in [o.id for o in outputs if o.archived]

    with pytest.raises(OutputAlreadyArchived):
        output_storage.archive_study_output("STA-mini", "20201014-1422eco-hello")

    output_storage.unarchive_study_output("STA-mini", "20201014-1422eco-hello")
    assert not output_storage.is_output_archived("STA-mini", "20201014-1422eco-hello")

    outputs = output_storage.list_outputs("STA-mini")
    assert "20201014-1422eco-hello" in [o.id for o in outputs if not o.archived]

    with pytest.raises(OutputAlreadyUnarchived):
        output_storage.unarchive_study_output("STA-mini", "20201014-1422eco-hello")

    with pytest.raises(StudyNotFoundError):
        output_storage.archive_study_output("non-existent", "non-existent")
    with pytest.raises(OutputNotFound):
        output_storage.archive_study_output("STA-mini", "non-existent")

    with pytest.raises(StudyNotFoundError):
        output_storage.unarchive_study_output("non-existent", "non-existent")
    with pytest.raises(OutputNotFound):
        output_storage.unarchive_study_output("STA-mini", "non-existent")


def test_output_copy(output_storage: IOutputStorage, tmp_path: Path) -> None:
    ##########################
    # Set Up
    ##########################

    # Create a study without outputs
    if output_storage.storage_type == OutputStorageType.IN_STUDY_FILE_TREE:
        studies_dir = tmp_path / "studies"
        sta_mini_path = studies_dir / "STA-mini"
        copy_path = studies_dir / "STA-mini-copy"
        shutil.copytree(sta_mini_path, copy_path, ignore=shutil.ignore_patterns("output"))
        (copy_path / "output").mkdir()
    else:
        (tmp_path / "outputs" / "STA-mini-copy").mkdir()

    ##########################
    # Test
    ##########################

    assert output_storage.list_outputs("STA-mini-copy") == []

    output_storage.copy_output("STA-mini", "STA-mini-copy", "20201014-1422eco-hello")
    outputs = output_storage.list_outputs("STA-mini-copy")
    assert [o.id for o in outputs] == ["20201014-1422eco-hello"]

    # Copy an archived output
    output_storage.archive_study_output("STA-mini", "20201014-1427eco")
    assert output_storage.is_output_archived("STA-mini", "20201014-1427eco")
    output_storage.copy_output("STA-mini", "STA-mini-copy", "20201014-1427eco")
    outputs = output_storage.list_outputs("STA-mini-copy")
    assert [o.id for o in outputs] == ["20201014-1422eco-hello", "20201014-1427eco"]
    assert output_storage.is_output_archived("STA-mini-copy", "20201014-1427eco")

    with pytest.raises(StudyNotFoundError):
        output_storage.copy_output("non-existent", "STA-mini-copy", "20201014-1427eco")
    with pytest.raises(StudyNotFoundError):
        output_storage.copy_output("STA-mini", "non-existent", "20201014-1427eco")
    with pytest.raises(OutputNotFound):
        output_storage.copy_output("STA-mini", "STA-mini-copy", "non-existent")

    with pytest.raises(OutputAlreadyExists):
        output_storage.copy_output("STA-mini", "STA-mini-copy", "20201014-1427eco")
    with pytest.raises(OutputAlreadyExists):
        output_storage.copy_output("STA-mini", "STA-mini-copy", "20201014-1422eco-hello")


def test_output_exists(output_storage: IOutputStorage) -> None:
    assert output_storage.output_exists("STA-mini", "20201014-1427eco")
    assert not output_storage.output_exists("STA-mini", "non-existent")

    output_storage.archive_study_output("STA-mini", "20201014-1427eco")
    assert output_storage.is_output_archived("STA-mini", "20201014-1427eco")
    assert output_storage.output_exists("STA-mini", "20201014-1427eco")

    with pytest.raises(StudyNotFoundError):
        output_storage.output_exists("non-existent", "20201014-1427eco")


def _count_files_in_dir(dir_path: Path) -> int:
    return sum(len(d[2]) for d in os.walk(dir_path))


def _count_files_in_zip(zip_path: Path) -> int:
    with zipfile.ZipFile(zip_path, "r") as zf:
        return len(zf.namelist())


def test_export_output(output_storage: IOutputStorage, tmp_path: Path) -> None:
    # We are just checking the count of files is correct as a proxy of a full content check
    expected_count = 79

    zip_path = tmp_path / "output.zip"
    output_storage.export_output("STA-mini", "20201014-1427eco", zip_path)
    assert zip_path.exists()
    assert _count_files_in_zip(zip_path) == expected_count

    # Check on archived study
    output_storage.archive_study_output("STA-mini", "20201014-1427eco")
    zip_path = tmp_path / "output2.zip"
    output_storage.export_output("STA-mini", "20201014-1427eco", zip_path)
    assert zip_path.exists()
    assert _count_files_in_zip(zip_path) == expected_count

    with pytest.raises(StudyNotFoundError):
        output_storage.export_output("non-existent", "20201014-1427eco", zip_path)
    with pytest.raises(OutputNotFound):
        output_storage.export_output("STA-mini", "non-existent", zip_path)


def test_write_output_to_dir(output_storage: IOutputStorage, tmp_path: Path) -> None:
    # We just checking the count of files is correct as a proxy of a full content check
    expected_count = 79

    export_path = tmp_path / "export"
    export_path.mkdir()
    output_storage.write_output_to_dir("STA-mini", "20201014-1427eco", export_path)
    expected_path = export_path / "20201014-1427eco"
    assert expected_path.is_dir()
    assert "about-the-study" in os.listdir(expected_path)
    assert _count_files_in_dir(expected_path) == expected_count

    # Check on archived study
    output_storage.archive_study_output("STA-mini", "20201014-1427eco")
    export_path = tmp_path / "export2"
    export_path.mkdir()
    output_storage.write_output_to_dir("STA-mini", "20201014-1427eco", export_path)
    expected_path = export_path / "20201014-1427eco"
    assert expected_path.is_dir()
    assert "about-the-study" in os.listdir(expected_path)
    assert _count_files_in_dir(expected_path) == expected_count

    with pytest.raises(StudyNotFoundError):
        output_storage.write_output_to_dir("non-existent", "20201014-1427eco", export_path)
    with pytest.raises(OutputNotFound):
        output_storage.write_output_to_dir("STA-mini", "non-existent", export_path)


def test_get_logs(output_storage: IOutputStorage, tmp_path: Path) -> None:
    # Will write fake logs to underlying output dir
    if output_storage.storage_type == OutputStorageType.IN_STUDY_FILE_TREE:
        outputs_path = tmp_path / "studies" / "STA-mini" / "output"
    else:
        outputs_path = tmp_path / "outputs" / "STA-mini"

    (outputs_path / "logs").mkdir()

    possible_log_paths = [
        outputs_path / "20201014-1427eco" / "antares-out.log",
        outputs_path / "20201014-1427eco" / "simulation.log",
    ]

    for log_path in possible_log_paths:
        log_path.write_text("some log 2")
        logs = output_storage.get_logs("STA-mini", "20201014-1427eco", LogType.STDOUT)
        assert logs == "some log 2"
        log_path.unlink()

        # Check invalid utf-8 characters are correctly replaced
        log_path.write_text("Caractère invalide", encoding="latin-1")
        logs = output_storage.get_logs("STA-mini", "20201014-1427eco", LogType.STDOUT)
        assert logs == "Caract�re invalide"
        log_path.unlink()


def test_import_output_directory(output_storage: IOutputStorage, tmp_path: Path, sta_mini_zip_path: Path) -> None:
    # Set Up
    if output_storage.storage_type == OutputStorageType.IN_STUDY_FILE_TREE:
        existing_output_dir = tmp_path / "studies" / "STA-mini" / "output" / "20201014-1422eco-hello"
        in_study = True
        (tmp_path / "studies" / "my-study").mkdir()
        expected_output_dir = tmp_path / "studies" / "my-study" / "output" / "20201014-1422eco-hello"
    else:
        existing_output_dir = tmp_path / "outputs" / "STA-mini" / "20201014-1422eco-hello"
        in_study = False
        (tmp_path / "outputs" / "my-study").mkdir()
        expected_output_dir = tmp_path / "outputs" / "my-study" / "20201014-1422eco-hello"

    # Import directory
    output_storage.import_output("my-study", existing_output_dir)

    # Cannot hard code the expected formatted date because it depends on the locale
    expected_date = utc_to_local("20201014-1222")

    assert expected_output_dir.exists()
    assert output_storage.list_outputs("my-study") == [
        OutputMetadata(id=f"{expected_date}eco-hello", in_study=in_study, archived=False)
    ]

    # Import directory with logs and suffix
    out_logs = tmp_path / "out.log"
    out_logs.write_text("some log")
    err_logs = tmp_path / "err.log"
    err_logs.write_text("some error")
    output_storage.import_output(
        "my-study", existing_output_dir, output_name_suffix="other", logs=SimulationLogs(out_logs, err_logs)
    )
    assert output_storage.list_outputs("my-study") == [
        OutputMetadata(id=f"{expected_date}eco-hello", in_study=in_study, archived=False),
        OutputMetadata(id=f"{expected_date}eco-other", in_study=in_study, archived=False),
    ]

    assert output_storage.get_logs("my-study", f"{expected_date}eco-other", LogType.STDOUT) == "some log"
    assert output_storage.get_logs("my-study", f"{expected_date}eco-other", LogType.STDERR) == "some error"


def test_import_output_zip_should_import_it_as_archived(
    output_storage: IOutputStorage, tmp_path: Path, sta_mini_zip_path: Path
) -> None:
    # Checks the "optimized path" for zipped outputs, see TODOs

    # Use the `20201014-1430adq-2` output as it's already zipped
    if output_storage.storage_type == OutputStorageType.IN_STUDY_FILE_TREE:
        studies_dir = tmp_path / "studies"
        (studies_dir / "my-study").mkdir()
        zip_path = studies_dir / "STA-mini" / "output" / "20201014-1430adq-2.zip"
        in_study = True
    else:
        outputs_dir = tmp_path / "outputs"
        (outputs_dir / "my-study").mkdir()
        zip_path = outputs_dir / "STA-mini" / "20201014-1430adq-2.zip"
        in_study = False

    # Import zip file
    output_id = output_storage.import_output("my-study", zip_path)

    # Cannot hard code the expected formatted date because it depends on the locale
    expected_date = utc_to_local("20201014-1230")

    assert output_id == f"{expected_date}adq"
    assert output_storage.list_outputs("my-study") == [
        OutputMetadata(id=f"{expected_date}adq", in_study=in_study, archived=True)
    ]

    # Import zip file with logs and suffix
    out_logs = tmp_path / "out.log"
    out_logs.write_text("some log")
    err_logs = tmp_path / "err.log"
    err_logs.write_text("some error")
    output_id = output_storage.import_output(
        "my-study", zip_path, output_name_suffix="other", logs=SimulationLogs(out_logs, err_logs)
    )
    assert output_id == f"{expected_date}adq-other"
    assert output_storage.list_outputs("my-study") == [
        OutputMetadata(id=f"{expected_date}adq-other", in_study=in_study, archived=True),
        OutputMetadata(id=f"{expected_date}adq", in_study=in_study, archived=True),
    ]

    output_storage.unarchive_study_output("my-study", f"{expected_date}adq-other")

    assert output_storage.get_logs("my-study", f"{expected_date}adq-other", LogType.STDOUT) == "some log"
    assert output_storage.get_logs("my-study", f"{expected_date}adq-other", LogType.STDERR) == "some error"


@pytest.mark.parametrize("archive_format", [ArchiveFormat.ZIP, ArchiveFormat.SEVEN_ZIP])
def test_import_output_archive_stream(
    output_storage: IOutputStorage,
    tmp_path: Path,
    sta_mini_zip_path: Path,
    archive_format: ArchiveFormat,
) -> None:
    # Checks the "optimized path" for zipped outputs, see TODOs

    # Extract one of the outputs of STA-mini to a directory and zip it
    studies_dir = tmp_path / "studies"

    study_dir = studies_dir / "my-study"
    study_dir.mkdir()

    if output_storage.storage_type == OutputStorageType.IN_STUDY_FILE_TREE:
        output_path = tmp_path / "studies" / "STA-mini/output/20201014-1422eco-hello"
        archive_path = tmp_path / f"import-output{archive_format}"
    else:
        print("ok")

    archive_dir(output_path, archive_path, True, archive_format)

    # Import archive stream
    with open(archive_path, "rb") as f:
        output_storage.import_output("my-study", f)

    # Cannot hard code the expected formatted date because it depends on the locale
    expected_date = utc_to_local("20201014-1222")

    assert output_storage.list_outputs("my-study") == [
        OutputMetadata(id=f"{expected_date}eco-hello", in_study=True, archived=False)
    ]
