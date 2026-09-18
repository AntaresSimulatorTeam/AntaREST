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
import json
from pathlib import Path

import polars as pl
import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.output.filestudy.download import build_matrix_aggregation_result as file_download
from antarest.output.filestudy.model import FileOutput, VariableDescription
from antarest.output.filestudy.variables import extract_variables_list
from antarest.output.model import StudyDownloadDTO, StudyDownloadType
from antarest.output.storage.v2.dbmodel import ELEMENT_TABLES, DbOutputMetadataV2, DbParquetVariable, IntList
from antarest.output.storage.v2.download import build_matrix_aggregation_result
from antarest.output.storage.v2.iteration import iterate_element_dfs
from antarest.output.storage.v2.metadata import ParquetOutputMetadata
from antarest.output.storage.v2.storage import V2OutputStorage
from antarest.output.storage.v2.variables_parsing import extract_output_variables_to_database
from antarest.output.storage.v2.variables_storage import create_parquet_files, parquet_output_dir
from antarest.study.model import MatrixFrequency
from tests.test_helpers.parquet_outputs import rich_output, write_matrix


@pytest.fixture(scope="module")
def source(tmp_path_factory) -> Path:
    return rich_output(tmp_path_factory.mktemp("parquet-contract") / "20260810-1420eco-test")


@pytest.fixture
def imported(source: Path, storage: V2OutputStorage, study_id: str) -> str:
    with db():
        return storage.import_output(study_id, source)


@pytest.mark.parametrize("frequency", list(MatrixFrequency))
@pytest.mark.parametrize(
    "kind,clusters",
    [
        (StudyDownloadType.AREA, False),
        (StudyDownloadType.AREA, True),
        (StudyDownloadType.DISTRICT, True),
        (StudyDownloadType.LINK, False),
    ],
)
def test_download_matches_file_storage(source, imported, storage, study_id, frequency, kind, clusters):
    # Include filtering, unknown variables and scenarios, and cluster-only requests.
    for years, elements, columns in [
        ([], [], []),
        ([2], [], []),
        ([7], [], []),
        ([1], ["es - fr" if kind == StudyDownloadType.LINK else "fr"], []),
        ([], [], ["FLOW" if kind == StudyDownloadType.LINK else "LOAD"]),
        ([], [], ["DOES_NOT_EXIST"]),
        ([], [], ["fr_a"]),
        ([], ["missing"], []),
    ]:
        selection = StudyDownloadDTO(
            type=kind, level=frequency, years=years, filter=elements, columns=columns, include_clusters=clusters
        )
        expected = file_download(source, selection)
        with db():
            actual = storage.get_matrix_aggregation_result(study_id, imported, selection)
        assert json.loads(actual.model_dump_json()) == json.loads(expected.model_dump_json())


def test_metadata_and_variables_list_survive_new_session(source, imported, storage, study_id):
    with db():
        assert storage.get_variables_list(study_id, imported) == extract_variables_list(source)
        output = storage._require_metadata(study_id, imported)
        variables = ParquetOutputMetadata(db.session, output.id).get_variables("mc-all", "thermal_cluster")
        assert VariableDescription("NP Cost - Euro", "NP Cost - Euro", "std") in variables
        assert VariableDescription(" ", None, "max") in variables
        assert "output_v2_variables" not in DbOutputMetadataV2.metadata.tables


@pytest.mark.parametrize("frequency", list(MatrixFrequency))
@pytest.mark.parametrize("aggregation,years", [("mc-ind", [1, 2]), ("mc-all", [0])])
def test_binding_constraint_values_and_metadata(imported, storage, study_id, frequency, aggregation, years):
    with db():
        output = storage._require_metadata(study_id, imported)
        items = list(
            iterate_element_dfs(
                ParquetOutputMetadata(db.session, output.id),
                parquet_output_dir(storage._variables_dir, study_id, imported),
                aggregation,
                "binding_constraint",
                frequency,
                [],
                ["bc"],
            )
        )
    assert [item.element.year for item in items] == years
    for item in items:
        assert item.element.element_id == "bc"
        assert item.variables == [VariableDescription("MARG. COST", "Euro", "EXP" if aggregation == "mc-all" else None)]
        assert item.data.to_series().to_list() == [float(item.element.year), None, float(item.element.year + 2)]


def test_column_names_are_not_metadata(source, imported, storage, study_id):
    directory = parquet_output_dir(storage._variables_dir, study_id, imported)
    for file in directory.glob("*.parquet"):
        frame = pl.read_parquet(file)
        frame.rename(
            {
                c: f"unrelated_{i}"
                for i, c in enumerate(frame.columns)
                if c not in ("area", "link", "cluster", "constraint", "timeId", "mcYear")
            }
        ).write_parquet(file)
    selection = StudyDownloadDTO(type=StudyDownloadType.AREA, level=MatrixFrequency.MONTHLY, include_clusters=True)
    with db():
        actual = storage.get_matrix_aggregation_result(study_id, imported, selection)
    assert actual == file_download(source, selection)


def test_output_lifecycle(source, imported, storage, study_id):
    selection = StudyDownloadDTO(type=StudyDownloadType.AREA, level=MatrixFrequency.MONTHLY, include_clusters=True)
    expected = file_download(source, selection)
    with db():
        source_id = storage._require_metadata(study_id, imported).id
        storage.copy_output(study_id, "other-study", imported)
        copy_id = storage._require_metadata("other-study", imported).id
        assert source_id != copy_id
        assert storage.get_matrix_aggregation_result("other-study", imported, selection) == expected
        storage.archive_study_output(study_id, imported)
        assert storage.get_variables_list(study_id, imported) == extract_variables_list(source)
        storage.unarchive_study_output(study_id, imported)
        assert storage.get_matrix_aggregation_result(study_id, imported, selection) == expected
        storage.delete_output(study_id, imported)
        for table in (DbParquetVariable, *ELEMENT_TABLES):
            assert db.session.scalar(select(func.count()).select_from(table).where(table.output_id == source_id)) == 0
        assert storage.get_matrix_aggregation_result("other-study", imported, selection) == expected


def test_legacy_metadata_rebuild(source, imported, storage, study_id):
    from sqlalchemy import delete

    with db():
        output = storage._require_metadata(study_id, imported)
        for table in (DbParquetVariable, *ELEMENT_TABLES):
            db.session.execute(delete(table).where(table.output_id == output.id))
        output.metadata_version = 0
        db.session.commit()
    with db():
        assert storage.get_variables_list(study_id, imported) == extract_variables_list(source)
        selection = StudyDownloadDTO(type=StudyDownloadType.LINK, level=MatrixFrequency.ANNUAL)
        assert storage.get_matrix_aggregation_result(study_id, imported, selection) == file_download(source, selection)
        assert storage._require_metadata(study_id, imported).metadata_version == 1


def test_empty_int_list_roundtrip(db_session: Session):
    dialect = db_session.get_bind().dialect
    column = IntList()
    assert column.process_result_value(column.process_bind_param([], dialect), dialect) == []


def test_membership_differs_by_year_and_frequency(tmp_path, db_session, parquet_metadata):
    # Unlike the simulator's usual layout, this checks that union columns never
    # invent variables for an object/year/frequency that did not contain them.
    source = tmp_path / "heterogeneous"
    for year, name in [(1, "first"), (2, "second")]:
        write_matrix(
            source / f"economy/mc-ind/{year:05}/areas/fr/values-monthly.txt",
            MatrixFrequency.MONTHLY,
            [VariableDescription(name, "MWh", None)],
        )
    write_matrix(
        source / "economy/mc-ind/00001/areas/fr/values-daily.txt",
        MatrixFrequency.DAILY,
        [VariableDescription("daily_only", None, None)],
    )
    metadata_row = DbOutputMetadataV2(
        study_id="other",
        output_name="other",
        mc_years=[1, 2],
        archived=False,
        mode="Economy",
        synthesis=False,
        by_year=True,
        nb_years=2,
        start_month=1,
        january_first_weekday=1,
        leap_year=False,
        start_day=1,
        end_day=365,
        first_weekday=1,
    )
    db_session.add(metadata_row)
    db_session.flush()
    output = FileOutput(source)
    extract_output_variables_to_database(db_session, metadata_row.id, output)
    metadata = ParquetOutputMetadata(db_session, metadata_row.id)
    target = tmp_path / "new-parquet-directory"
    create_parquet_files(metadata, output, target)
    selection = StudyDownloadDTO(type=StudyDownloadType.AREA, level=MatrixFrequency.MONTHLY)
    result = build_matrix_aggregation_result(metadata, target, selection)
    assert [v.name for v in result.data[0].data["1"]] == ["first"]
    assert [v.name for v in result.data[0].data["2"]] == ["second"]
    selection.level = MatrixFrequency.DAILY
    result = build_matrix_aggregation_result(metadata, target, selection)
    assert list(result.data[0].data) == ["1"]
    assert result.data[0].data["1"][0].name == "daily_only"


def test_failed_import_leaves_no_partial_output(source, storage, study_id, mocker):
    mocker.patch.object(storage, "_save_logs", side_effect=RuntimeError("simulated import failure"))
    with db():
        with pytest.raises(RuntimeError, match="simulated import failure"):
            storage.import_output(study_id, source)
        assert storage.list_outputs(study_id) == []
        assert storage._archive_storage.list_files() == []
        for table in (DbParquetVariable, *ELEMENT_TABLES):
            assert db.session.scalar(select(func.count()).select_from(table)) == 0
    assert not list(storage._variables_dir.glob("*.parquet"))
    assert not list(storage._variables_dir.iterdir())


def test_failed_copy_preserves_source(source, imported, storage, study_id, mocker):
    selection = StudyDownloadDTO(type=StudyDownloadType.LINK, level=MatrixFrequency.MONTHLY)
    mocker.patch("antarest.output.storage.v2.storage.shutil.copytree", side_effect=OSError("copy failed"))
    with db():
        with pytest.raises(OSError, match="copy failed"):
            storage.copy_output(study_id, "failed-copy", imported)
        assert storage.list_outputs("failed-copy") == []
        assert storage.get_matrix_aggregation_result(study_id, imported, selection) == file_download(source, selection)
        assert not storage._archive_storage.file_exists(f"failed-copy-{imported}")


def test_archived_legacy_output_rebuilds_only_metadata(source, imported, storage, study_id, mocker):
    with db():
        storage.archive_study_output(study_id, imported)
        output = storage._require_metadata(study_id, imported)
        output.metadata_version = 0
        db.session.commit()
    writer = mocker.patch("antarest.output.storage.v2.storage.create_parquet_files")
    with db():
        assert storage.get_variables_list(study_id, imported) == extract_variables_list(source)
        assert storage.is_output_archived(study_id, imported)
    writer.assert_not_called()
    assert not parquet_output_dir(storage._variables_dir, study_id, imported).exists()


def test_failed_legacy_rebuild_preserves_previous_files(imported, storage, study_id, mocker):
    directory = parquet_output_dir(storage._variables_dir, study_id, imported)
    before = {p.name: p.read_bytes() for p in directory.iterdir()}
    with db():
        output = storage._require_metadata(study_id, imported)
        output.metadata_version = 0
        db.session.commit()
    mocker.patch("antarest.output.storage.v2.storage.create_parquet_files", side_effect=OSError("write failed"))
    with db():
        with pytest.raises(OSError, match="write failed"):
            storage.get_variables_list(study_id, imported)
        assert storage._require_metadata(study_id, imported).metadata_version == 0
    assert {p.name: p.read_bytes() for p in directory.iterdir()} == before
