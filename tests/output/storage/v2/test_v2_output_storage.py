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
import shutil
import uuid
import zipfile
from pathlib import Path
from unittest.mock import Mock

import polars as pl
import pytest
from sqlalchemy import Engine

from antarest.core.utils.archives import ArchiveFormat, archive_dir
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.fastapi_sqlalchemy.middleware import init_db_singleton
from antarest.launcher.adapters.abstractlauncher import SimulationLogs
from antarest.launcher.model import LogType
from antarest.lfs.dir_lfs import DirLargeFileStorage
from antarest.lfs.lfs import ILargeFileStorage
from antarest.output.model import MCAllAreasFile
from antarest.output.storage.v2.repository import OutputV2Repository
from antarest.output.storage.v2.storage import V2OutputStorage
from antarest.output.storage.v2.variables_storage import parquet_output_dir
from antarest.study.model import MatrixFrequency, MatrixIndex, Study
from antarest.study.repository import StudyMetadataRepository
from tests.test_helpers.dates import utc_to_local

EXPECTED_DATE = utc_to_local("20201014-1227")


@pytest.fixture
def init_db(db_engine: Engine) -> None:
    init_db_singleton(custom_engine=db_engine)


@pytest.fixture
def study_repo(init_db) -> StudyMetadataRepository:
    return StudyMetadataRepository(cache_service=Mock())


@pytest.fixture
def output_repo(init_db) -> OutputV2Repository:
    return OutputV2Repository()


@pytest.fixture(scope="session")
def sta_mini_zip_path(project_path: Path) -> Path:
    return project_path / "examples/studies/STA-mini.zip"


@pytest.fixture(scope="session")
def output_path(tmp_path_factory: pytest.TempPathFactory, sta_mini_zip_path: Path) -> Path:
    tmp_dir = tmp_path_factory.mktemp(basename=f"unzipped-output-{uuid.uuid4()}")

    with zipfile.ZipFile(sta_mini_zip_path, "r") as zf:
        zf.extractall(tmp_dir)
    return tmp_dir / "STA-mini" / "output" / "20201014-1427eco"


@pytest.fixture
def study_id(study_repo: StudyMetadataRepository) -> str:
    with db():
        # The FK constraints enforces us to create a study first.
        study_repo.save(Study(id="my-study", name="name", version="9.2", path=""))
    return "my-study"


@pytest.fixture
def lfs(tmp_path: Path) -> ILargeFileStorage:
    return DirLargeFileStorage(tmp_path / "lfs")


@pytest.fixture
def storage(
    tmp_path: Path, study_repo: StudyMetadataRepository, output_repo: OutputV2Repository, lfs: ILargeFileStorage
) -> V2OutputStorage:
    storage_tmp_dir = tmp_path / "storage" / "tmp"
    variables_dir = tmp_path / "variables"
    storage = V2OutputStorage(
        archive_storage=lfs, tmp_dir=storage_tmp_dir, repository=output_repo, variables_dir=variables_dir
    )
    return storage


def test_storage(
    tmp_path: Path,
    storage: V2OutputStorage,
    lfs: ILargeFileStorage,
    study_id: str,
    output_path: Path,
):
    with db():
        # Check there is no output at first for that study
        assert not storage.output_exists(study_id="my-study", output_id=f"{EXPECTED_DATE}eco")
        assert storage.list_outputs(study_id="my-study") == []

        # Import output
        output_name = storage.import_output("my-study", output_path)
        assert output_name == f"{EXPECTED_DATE}eco"

        # Check output exists
        assert storage.output_exists(study_id="my-study", output_id=f"{EXPECTED_DATE}eco")
        assert not storage.is_output_archived(study_id="my-study", output_id=f"{EXPECTED_DATE}eco")

        # Check output appears in list of study outputs
        study_outputs = storage.list_outputs(study_id="my-study")
        assert len(study_outputs) == 1
        study_output = study_outputs[0]
        assert study_output.id == f"{EXPECTED_DATE}eco"
        assert not study_output.archived
        assert len(lfs.list_files()) == 1

        # Check output export works
        export_path = tmp_path / "exported.zip"
        storage.export_output(study_id="my-study", output_id=f"{EXPECTED_DATE}eco", target=export_path)
        assert export_path.exists()
        assert zipfile.is_zipfile(export_path)

        # Archive output
        storage.archive_study_output(study_id="my-study", output_id=f"{EXPECTED_DATE}eco")
        assert storage.is_output_archived(study_id="my-study", output_id=f"{EXPECTED_DATE}eco")

        # Check we can still download it
        export_path = tmp_path / "exported-2.zip"
        storage.export_output(study_id="my-study", output_id=f"{EXPECTED_DATE}eco", target=export_path)
        assert export_path.exists()
        assert zipfile.is_zipfile(export_path)

        # Delete output
        storage.delete_output(study_id="my-study", output_id=f"{EXPECTED_DATE}eco")
        assert not storage.output_exists(study_id="my-study", output_id=f"{EXPECTED_DATE}eco")
        assert storage.list_outputs(study_id="my-study") == []
        assert lfs.list_files() == []


def create_archive(archive_format: ArchiveFormat, nested: bool, output_path: Path, tmp_path: Path) -> Path:
    """
    Creates an archive containing the output files, possibly with an additional directory level if nested is True
    """
    if nested:
        nested_output_path = tmp_path / "output"
        shutil.copytree(output_path, nested_output_path / "nested")
        output_path = nested_output_path
    archive_path = tmp_path / f"archive{archive_format}"
    archive_dir(output_path, archive_path, remove_source_dir=False, archive_format=archive_format)
    return archive_path


@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize("archive_format", [ArchiveFormat.ZIP, ArchiveFormat.SEVEN_ZIP])
def test_import_archive(
    storage: V2OutputStorage,
    study_id: str,
    output_path: Path,
    archive_format: ArchiveFormat,
    nested: bool,
    tmp_path: Path,
):
    archive_path = create_archive(archive_format, nested, output_path, tmp_path)
    with db():
        output_name = storage.import_output(study_id, archive_path)

    assert output_name == f"{EXPECTED_DATE}eco"
    with db():
        assert storage.output_exists(study_id=study_id, output_id=f"{EXPECTED_DATE}eco")
        assert not storage.is_output_archived(study_id=study_id, output_id=f"{EXPECTED_DATE}eco")


@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize("archive_format", [ArchiveFormat.ZIP, ArchiveFormat.SEVEN_ZIP])
def test_import_archive_stream(
    storage: V2OutputStorage,
    study_id: str,
    output_path: Path,
    archive_format: ArchiveFormat,
    nested: bool,
    tmp_path: Path,
):
    archive_path = create_archive(archive_format, nested, output_path, tmp_path)
    with db():
        with open(archive_path, "rb") as archive_io:
            output_name = storage.import_output(study_id, archive_io)

    assert output_name == f"{EXPECTED_DATE}eco"
    with db():
        assert storage.output_exists(study_id=study_id, output_id=f"{EXPECTED_DATE}eco")
        assert not storage.is_output_archived(study_id=study_id, output_id=f"{EXPECTED_DATE}eco")


def test_import_output_with_existing_logs(storage: V2OutputStorage, study_id: str, output_path: Path) -> None:
    with db():
        output_name = storage.import_output(study_id, output_path)
        assert output_name == f"{EXPECTED_DATE}eco"

        assert storage.output_exists(study_id, f"{EXPECTED_DATE}eco")

        out_logs = storage.get_logs(study_id, f"{EXPECTED_DATE}eco", LogType.STDOUT)
        assert len(out_logs.splitlines()) == 239
        assert storage.get_logs(study_id, f"{EXPECTED_DATE}eco", LogType.STDERR) == ""


def test_import_output_override_logs(
    storage: V2OutputStorage, study_id: str, output_path: Path, tmp_path: Path
) -> None:
    out_path = tmp_path / "out.log"
    err_path = tmp_path / "err.log"
    out_path.write_text("out log")
    err_path.write_text("err log")
    with db():
        output_name = storage.import_output(study_id, output_path, logs=SimulationLogs(out_path, err_path))
        assert output_name == f"{EXPECTED_DATE}eco"

        assert storage.output_exists(study_id, f"{EXPECTED_DATE}eco")

        assert storage.get_logs(study_id, f"{EXPECTED_DATE}eco", LogType.STDOUT) == "out log"
        assert storage.get_logs(study_id, f"{EXPECTED_DATE}eco", LogType.STDERR) == "err log"


def test_import_output_time_index(storage: V2OutputStorage, study_id: str, output_path: Path) -> None:
    with db():
        output_name = storage.import_output(study_id, output_path)
        assert output_name == f"{EXPECTED_DATE}eco"

        assert storage.output_exists(study_id, f"{EXPECTED_DATE}eco")

        hourly_index = storage.get_output_time_index(study_id, f"{EXPECTED_DATE}eco", MatrixFrequency.HOURLY)
        assert hourly_index == MatrixIndex(
            start_date="2018-01-01 00:00:00", steps=168, first_week_size=7, level=MatrixFrequency.HOURLY
        )
        daily_index = storage.get_output_time_index(study_id, f"{EXPECTED_DATE}eco", MatrixFrequency.DAILY)
        assert daily_index == MatrixIndex(
            start_date="2018-01-01 00:00:00", steps=7, first_week_size=7, level=MatrixFrequency.DAILY
        )
        weekly_index = storage.get_output_time_index(study_id, f"{EXPECTED_DATE}eco", MatrixFrequency.WEEKLY)
        assert weekly_index == MatrixIndex(
            start_date="2018-01-01 00:00:00", steps=1, first_week_size=7, level=MatrixFrequency.WEEKLY
        )
        monthly_index = storage.get_output_time_index(study_id, f"{EXPECTED_DATE}eco", MatrixFrequency.MONTHLY)
        assert monthly_index == MatrixIndex(
            start_date="2018-01-01 00:00:00", steps=1, first_week_size=7, level=MatrixFrequency.MONTHLY
        )


def test_import_output_variable_list(storage: V2OutputStorage, study_id: str, output_path: Path) -> None:
    with db():
        output_name = storage.import_output(study_id, output_path)
        assert output_name == f"{EXPECTED_DATE}eco"

        assert storage.output_exists(study_id, f"{EXPECTED_DATE}eco")

        variables_list = storage.get_variables_list(study_id, f"{EXPECTED_DATE}eco")
        assert variables_list.model_dump() == {
            "mc_all": {
                "areas": [
                    {
                        "name": "de",
                        "renewable_clusters": [],
                        "short_term_storages": [],
                        "thermal_clusters": [
                            {"name": "01_solar", "variables": ["MWh", "NODU", "NP Cost - Euro"]},
                            {"name": "02_wind_on", "variables": ["MWh", "NODU", "NP Cost - Euro"]},
                            {"name": "03_wind_off", "variables": ["MWh", "NODU", "NP Cost - Euro"]},
                            {"name": "04_res", "variables": ["MWh", "NODU", "NP Cost - Euro"]},
                            {"name": "05_nuclear", "variables": ["MWh", "NODU", "NP Cost - Euro"]},
                            {"name": "06_coal", "variables": ["MWh", "NODU", "NP Cost - Euro"]},
                            {"name": "07_gas", "variables": ["MWh", "NODU", "NP Cost - Euro"]},
                            {"name": "08_non-res", "variables": ["MWh", "NODU", "NP Cost - Euro"]},
                            {"name": "09_hydro_pump", "variables": ["MWh", "NODU", "NP Cost - Euro"]},
                        ],
                        "variables": [
                            "AVL DTG EXP",
                            "AVL DTG MAX",
                            "AVL DTG MIN",
                            "AVL DTG STD",
                            "BALANCE EXP",
                            "BALANCE MAX",
                            "BALANCE MIN",
                            "BALANCE STD",
                            "CO2 EMIS. EXP",
                            "COAL EXP",
                            "COAL MAX",
                            "COAL MIN",
                            "COAL STD",
                            "DTG MRG EXP",
                            "DTG MRG MAX",
                            "DTG MRG MIN",
                            "DTG MRG STD",
                            "GAS EXP",
                            "GAS MAX",
                            "GAS MIN",
                            "GAS STD",
                            "H. COST EXP",
                            "H. COST MAX",
                            "H. COST MIN",
                            "H. COST STD",
                            "H. INFL EXP",
                            "H. INFL MAX",
                            "H. INFL MIN",
                            "H. INFL STD",
                            "H. LEV EXP",
                            "H. LEV MAX",
                            "H. LEV MIN",
                            "H. LEV STD",
                            "H. OVFL EXP",
                            "H. OVFL MAX",
                            "H. OVFL MIN",
                            "H. OVFL STD",
                            "H. PUMP EXP",
                            "H. PUMP MAX",
                            "H. PUMP MIN",
                            "H. PUMP STD",
                            "H. ROR EXP",
                            "H. ROR MAX",
                            "H. ROR MIN",
                            "H. ROR STD",
                            "H. STOR EXP",
                            "H. STOR MAX",
                            "H. STOR MIN",
                            "H. STOR STD",
                            "H. VAL EXP",
                            "H. VAL MAX",
                            "H. VAL MIN",
                            "H. VAL STD",
                            "LIGNITE EXP",
                            "LIGNITE MAX",
                            "LIGNITE MIN",
                            "LIGNITE STD",
                            "LOAD EXP",
                            "LOAD MAX",
                            "LOAD MIN",
                            "LOAD STD",
                            "LOLD EXP",
                            "LOLD MAX",
                            "LOLD MIN",
                            "LOLD STD",
                            "LOLP VALUES",
                            "MAX MRG EXP",
                            "MAX MRG MAX",
                            "MAX MRG MIN",
                            "MAX MRG STD",
                            "MISC. DTG EXP",
                            "MISC. DTG MAX",
                            "MISC. DTG MIN",
                            "MISC. DTG STD",
                            "MISC. NDG EXP",
                            "MIX. FUEL EXP",
                            "MIX. FUEL MAX",
                            "MIX. FUEL MIN",
                            "MIX. FUEL STD",
                            "MRG. PRICE EXP",
                            "MRG. PRICE MAX",
                            "MRG. PRICE MIN",
                            "MRG. PRICE STD",
                            "NODU EXP",
                            "NODU MAX",
                            "NODU MIN",
                            "NODU STD",
                            "NP COST EXP",
                            "NP COST MAX",
                            "NP COST MIN",
                            "NP COST STD",
                            "NUCLEAR EXP",
                            "NUCLEAR MAX",
                            "NUCLEAR MIN",
                            "NUCLEAR STD",
                            "OIL EXP",
                            "OIL MAX",
                            "OIL MIN",
                            "OIL STD",
                            "OP. COST EXP",
                            "OP. COST MAX",
                            "OP. COST MIN",
                            "OP. COST STD",
                            "OV. COST EXP",
                            "PSP EXP",
                            "ROW BAL. VALUES",
                            "SOLAR EXP",
                            "SOLAR MAX",
                            "SOLAR MIN",
                            "SOLAR STD",
                            "SPIL. ENRG EXP",
                            "SPIL. ENRG MAX",
                            "SPIL. ENRG MIN",
                            "SPIL. ENRG STD",
                            "UNSP. ENRG EXP",
                            "UNSP. ENRG MAX",
                            "UNSP. ENRG MIN",
                            "UNSP. ENRG STD",
                            "WIND EXP",
                            "WIND MAX",
                            "WIND MIN",
                            "WIND STD",
                        ],
                    },
                    {
                        "name": "es",
                        "renewable_clusters": [],
                        "short_term_storages": [],
                        "thermal_clusters": [
                            {"name": "01_solar", "variables": ["MWh", "NODU", "NP Cost - Euro"]},
                            {"name": "02_wind_on", "variables": ["MWh", "NODU", "NP Cost - Euro"]},
                            {"name": "03_wind_off", "variables": ["MWh", "NODU", "NP Cost - Euro"]},
                            {"name": "04_res", "variables": ["MWh", "NODU", "NP Cost - Euro"]},
                            {"name": "05_nuclear", "variables": ["MWh", "NODU", "NP Cost - Euro"]},
                            {"name": "06_coal", "variables": ["MWh", "NODU", "NP Cost - Euro"]},
                            {"name": "07_gas", "variables": ["MWh", "NODU", "NP Cost - Euro"]},
                            {"name": "08_non-res", "variables": ["MWh", "NODU", "NP Cost - Euro"]},
                            {"name": "09_hydro_pump", "variables": ["MWh", "NODU", "NP Cost - Euro"]},
                        ],
                        "variables": [
                            "AVL DTG EXP",
                            "AVL DTG MAX",
                            "AVL DTG MIN",
                            "AVL DTG STD",
                            "BALANCE EXP",
                            "BALANCE MAX",
                            "BALANCE MIN",
                            "BALANCE STD",
                            "CO2 EMIS. EXP",
                            "COAL EXP",
                            "COAL MAX",
                            "COAL MIN",
                            "COAL STD",
                            "DTG MRG EXP",
                            "DTG MRG MAX",
                            "DTG MRG MIN",
                            "DTG MRG STD",
                            "GAS EXP",
                            "GAS MAX",
                            "GAS MIN",
                            "GAS STD",
                            "H. COST EXP",
                            "H. COST MAX",
                            "H. COST MIN",
                            "H. COST STD",
                            "H. INFL EXP",
                            "H. INFL MAX",
                            "H. INFL MIN",
                            "H. INFL STD",
                            "H. LEV EXP",
                            "H. LEV MAX",
                            "H. LEV MIN",
                            "H. LEV STD",
                            "H. OVFL EXP",
                            "H. OVFL MAX",
                            "H. OVFL MIN",
                            "H. OVFL STD",
                            "H. PUMP EXP",
                            "H. PUMP MAX",
                            "H. PUMP MIN",
                            "H. PUMP STD",
                            "H. ROR EXP",
                            "H. ROR MAX",
                            "H. ROR MIN",
                            "H. ROR STD",
                            "H. STOR EXP",
                            "H. STOR MAX",
                            "H. STOR MIN",
                            "H. STOR STD",
                            "H. VAL EXP",
                            "H. VAL MAX",
                            "H. VAL MIN",
                            "H. VAL STD",
                            "LIGNITE EXP",
                            "LIGNITE MAX",
                            "LIGNITE MIN",
                            "LIGNITE STD",
                            "LOAD EXP",
                            "LOAD MAX",
                            "LOAD MIN",
                            "LOAD STD",
                            "LOLD EXP",
                            "LOLD MAX",
                            "LOLD MIN",
                            "LOLD STD",
                            "LOLP VALUES",
                            "MAX MRG EXP",
                            "MAX MRG MAX",
                            "MAX MRG MIN",
                            "MAX MRG STD",
                            "MISC. DTG EXP",
                            "MISC. DTG MAX",
                            "MISC. DTG MIN",
                            "MISC. DTG STD",
                            "MISC. NDG EXP",
                            "MIX. FUEL EXP",
                            "MIX. FUEL MAX",
                            "MIX. FUEL MIN",
                            "MIX. FUEL STD",
                            "MRG. PRICE EXP",
                            "MRG. PRICE MAX",
                            "MRG. PRICE MIN",
                            "MRG. PRICE STD",
                            "NODU EXP",
                            "NODU MAX",
                            "NODU MIN",
                            "NODU STD",
                            "NP COST EXP",
                            "NP COST MAX",
                            "NP COST MIN",
                            "NP COST STD",
                            "NUCLEAR EXP",
                            "NUCLEAR MAX",
                            "NUCLEAR MIN",
                            "NUCLEAR STD",
                            "OIL EXP",
                            "OIL MAX",
                            "OIL MIN",
                            "OIL STD",
                            "OP. COST EXP",
                            "OP. COST MAX",
                            "OP. COST MIN",
                            "OP. COST STD",
                            "OV. COST EXP",
                            "PSP EXP",
                            "ROW BAL. VALUES",
                            "SOLAR EXP",
                            "SOLAR MAX",
                            "SOLAR MIN",
                            "SOLAR STD",
                            "SPIL. ENRG EXP",
                            "SPIL. ENRG MAX",
                            "SPIL. ENRG MIN",
                            "SPIL. ENRG STD",
                            "UNSP. ENRG EXP",
                            "UNSP. ENRG MAX",
                            "UNSP. ENRG MIN",
                            "UNSP. ENRG STD",
                            "WIND EXP",
                            "WIND MAX",
                            "WIND MIN",
                            "WIND STD",
                        ],
                    },
                    {
                        "name": "fr",
                        "renewable_clusters": [],
                        "short_term_storages": [],
                        "thermal_clusters": [],
                        "variables": [],
                    },
                    {
                        "name": "it",
                        "renewable_clusters": [],
                        "short_term_storages": [],
                        "thermal_clusters": [],
                        "variables": [],
                    },
                ],
                "links": [
                    {"area_1_name": "de", "area_2_name": "fr", "variables": []},
                    {"area_1_name": "es", "area_2_name": "fr", "variables": []},
                    {"area_1_name": "fr", "area_2_name": "it", "variables": []},
                ],
            },
            "mc_ind": {"areas": [], "links": []},
        }


@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize("archive_format", [ArchiveFormat.ZIP, ArchiveFormat.SEVEN_ZIP])
def test_write_imported_output_to_dir(
    storage: V2OutputStorage,
    study_id: str,
    output_path: Path,
    archive_format: ArchiveFormat,
    nested: bool,
    tmp_path: Path,
):
    archive_path = create_archive(archive_format, nested, output_path, tmp_path)
    with db():
        with open(archive_path, "rb") as archive_io:
            output_name = storage.import_output(study_id, archive_io)

    assert output_name == f"{EXPECTED_DATE}eco"
    with db():
        assert storage.output_exists(study_id=study_id, output_id=f"{EXPECTED_DATE}eco")
        parent_dir = tmp_path / "export"
        parent_dir.mkdir()
        storage.write_output_to_dir(study_id, f"{EXPECTED_DATE}eco", parent_dir)
        assert (parent_dir / f"{EXPECTED_DATE}eco").exists()
        assert (parent_dir / f"{EXPECTED_DATE}eco" / "about-the-study" / "parameters.ini").exists()


def test_copy_output(
    study_repo: StudyMetadataRepository,
    storage: V2OutputStorage,
    study_id: str,
    output_path: Path,
    tmp_path: Path,
):
    with db():
        study_repo.save(Study(id="my-copy", name="name", version="9.2", path=""))

        output_name = storage.import_output(study_id, output_path)
        assert output_name == f"{EXPECTED_DATE}eco"

        assert storage.output_exists(study_id, f"{EXPECTED_DATE}eco")

        storage.copy_output(study_id, "my-copy", f"{EXPECTED_DATE}eco")

        assert storage.output_exists(study_id, f"{EXPECTED_DATE}eco")
        assert storage.output_exists("my-copy", f"{EXPECTED_DATE}eco")

        # Verify the copied output has the same details
        src_details = storage.get_output_details(study_id, f"{EXPECTED_DATE}eco")
        copy_details = storage.get_output_details("my-copy", f"{EXPECTED_DATE}eco")
        assert src_details == copy_details

        # Verify the copied output has the same logs
        src_out_logs = storage.get_logs(study_id, f"{EXPECTED_DATE}eco", LogType.STDOUT)
        copy_out_logs = storage.get_logs("my-copy", f"{EXPECTED_DATE}eco", LogType.STDOUT)
        assert copy_out_logs == src_out_logs
        assert len(copy_out_logs.splitlines()) == 239

        src_err_logs = storage.get_logs(study_id, f"{EXPECTED_DATE}eco", LogType.STDERR)
        copy_err_logs = storage.get_logs("my-copy", f"{EXPECTED_DATE}eco", LogType.STDERR)
        assert copy_err_logs == src_err_logs
        assert copy_err_logs == ""

        # Verify the copied output has the same variables list
        src_variables = storage.get_variables_list(study_id, f"{EXPECTED_DATE}eco")
        copy_variables = storage.get_variables_list("my-copy", f"{EXPECTED_DATE}eco")
        assert copy_variables.model_dump() == src_variables.model_dump()

        # Verify the copied output can be exported
        export_path = tmp_path / "copied-export.zip"
        storage.export_output("my-copy", f"{EXPECTED_DATE}eco", target=export_path)
        assert export_path.exists()
        assert zipfile.is_zipfile(export_path)

        # Verify the copied output can be archived and unarchived
        assert not storage.is_output_archived("my-copy", f"{EXPECTED_DATE}eco")
        storage.archive_study_output("my-copy", f"{EXPECTED_DATE}eco")
        assert storage.is_output_archived("my-copy", f"{EXPECTED_DATE}eco")
        storage.unarchive_study_output("my-copy", f"{EXPECTED_DATE}eco")
        assert not storage.is_output_archived("my-copy", f"{EXPECTED_DATE}eco")

        # Verify the copied output has the same time index
        src_hourly_index = storage.get_output_time_index(study_id, f"{EXPECTED_DATE}eco", MatrixFrequency.HOURLY)
        copy_hourly_index = storage.get_output_time_index("my-copy", f"{EXPECTED_DATE}eco", MatrixFrequency.HOURLY)
        assert copy_hourly_index == src_hourly_index

        # Verify the copied output can be written to directory
        parent_dir = tmp_path / "copied-export-dir"
        parent_dir.mkdir()
        storage.write_output_to_dir("my-copy", f"{EXPECTED_DATE}eco", parent_dir)
        assert (parent_dir / f"{EXPECTED_DATE}eco").exists()
        assert (parent_dir / f"{EXPECTED_DATE}eco" / "about-the-study" / "parameters.ini").exists()


def test_import_creates_parquet_files(
    storage: V2OutputStorage,
    study_id: str,
    output_path: Path,
    tmp_path: Path,
):
    with db():
        output_name = storage.import_output(study_id, output_path)

    variables_dir = tmp_path / "variables"
    parquet_dir = parquet_output_dir(variables_dir, study_id, output_name)
    assert parquet_dir.exists()

    parquet_files = [f.name for f in parquet_dir.iterdir()]
    assert "mc-all_areas_daily.parquet" in parquet_files
    assert "mc-all_areas_monthly.parquet" in parquet_files
    assert "mc-all_thermal_clusters_daily.parquet" in parquet_files
    assert "mc-all_thermal_clusters_monthly.parquet" in parquet_files

    assert not any(f.startswith("mc-ind") for f in parquet_files)
    assert not any("links" in f for f in parquet_files)


def test_parquet_areas_content(
    storage: V2OutputStorage,
    study_id: str,
    output_path: Path,
    tmp_path: Path,
):
    with db():
        output_name = storage.import_output(study_id, output_path)

    variables_dir = tmp_path / "variables"
    parquet_dir = parquet_output_dir(variables_dir, study_id, output_name)
    areas_daily = pl.read_parquet(parquet_dir / "mc-all_areas_daily.parquet")

    assert set(areas_daily["area"]) == {"de", "es"}
    assert "area" in areas_daily.columns
    assert "timeId" in areas_daily.columns
    assert "LOAD EXP" in areas_daily.columns
    assert "BALANCE EXP" in areas_daily.columns


def test_parquet_thermal_clusters_content(
    storage: V2OutputStorage,
    study_id: str,
    output_path: Path,
    tmp_path: Path,
):
    with db():
        output_name = storage.import_output(study_id, output_path)

    variables_dir = tmp_path / "variables"
    parquet_dir = parquet_output_dir(variables_dir, study_id, output_name)
    clusters_daily = pl.read_parquet(parquet_dir / "mc-all_thermal_clusters_daily.parquet")

    assert "cluster" in clusters_daily.columns
    assert "area" in clusters_daily.columns
    assert "timeId" in clusters_daily.columns

    cluster_names = set(clusters_daily["cluster"])
    assert "01_solar" in cluster_names


def test_delete_removes_parquet(
    storage: V2OutputStorage,
    study_id: str,
    output_path: Path,
    tmp_path: Path,
):
    with db():
        output_name = storage.import_output(study_id, output_path)

    variables_dir = tmp_path / "variables"
    parquet_dir = parquet_output_dir(variables_dir, study_id, output_name)
    assert parquet_dir.exists()

    with db():
        storage.delete_output(study_id, output_name)

    assert not parquet_dir.exists()


def test_copy_output_copies_parquet(
    study_repo: StudyMetadataRepository,
    storage: V2OutputStorage,
    study_id: str,
    output_path: Path,
    tmp_path: Path,
):
    with db():
        study_repo.save(Study(id="copy-target", name="name", version="9.2", path=""))
        output_name = storage.import_output(study_id, output_path)
        storage.copy_output(study_id, "copy-target", output_name)

    variables_dir = tmp_path / "variables"
    src_dir = parquet_output_dir(variables_dir, study_id, output_name)
    dst_dir = parquet_output_dir(variables_dir, "copy-target", output_name)

    assert src_dir.exists()
    assert dst_dir.exists()
    src_files = [f.name for f in src_dir.iterdir()]
    dst_files = [f.name for f in dst_dir.iterdir()]
    assert src_files == dst_files


def test_aggregate_areas_values(
    storage: V2OutputStorage,
    study_id: str,
    output_path: Path,
):
    with db():
        output_name = storage.import_output(study_id, output_path)

        dfs = list(
            storage.iterate_output_table(
                study_id,
                output_name,
                query_file=MCAllAreasFile.VALUES,
                frequency=MatrixFrequency.DAILY,
                ids_to_consider=[],
                columns_names=[],
                transform_columns_headers=True,
            )
        )
        assert len(dfs) >= 1
        df = pl.concat(dfs)

        assert "area" in df.columns
        assert "timeId" in df.columns
        assert "LOAD EXP" in df.columns
        assert set(df["area"]) == {"de", "es"}


def test_aggregate_with_area_filter(
    storage: V2OutputStorage,
    study_id: str,
    output_path: Path,
):
    with db():
        output_name = storage.import_output(study_id, output_path)

        dfs = list(
            storage.iterate_output_table(
                study_id,
                output_name,
                query_file=MCAllAreasFile.VALUES,
                frequency=MatrixFrequency.DAILY,
                ids_to_consider=["de"],
                columns_names=[],
                transform_columns_headers=True,
            )
        )

        df = pl.concat(dfs)
        assert set(df["area"]) == {"de"}


def test_aggregate_with_column_filter(
    storage: V2OutputStorage,
    study_id: str,
    output_path: Path,
):
    with db():
        output_name = storage.import_output(study_id, output_path)

        dfs = storage.iterate_output_table(
            study_id,
            output_name,
            query_file=MCAllAreasFile.VALUES,
            frequency=MatrixFrequency.DAILY,
            ids_to_consider=[],
            columns_names=["load"],
        )
        df = pl.concat(dfs)

        variable_cols = [c for c in df.columns if c not in {"area", "timeId", "mcYear", "cluster"}]
        assert all("LOAD" in c for c in variable_cols)


def test_aggregate_thermal_clusters(
    storage: V2OutputStorage,
    study_id: str,
    output_path: Path,
):
    with db():
        output_name = storage.import_output(study_id, output_path)

        dfs = list(
            storage.iterate_output_table(
                study_id,
                output_name,
                query_file=MCAllAreasFile.DETAILS,
                frequency=MatrixFrequency.DAILY,
                ids_to_consider=[],
                columns_names=[],
                transform_columns_headers=True,
            )
        )
        df = pl.concat(dfs)

        assert "area" in df.columns
        assert "cluster" in df.columns
        assert "timeId" in df.columns
        assert "01_solar" in df["cluster"]
