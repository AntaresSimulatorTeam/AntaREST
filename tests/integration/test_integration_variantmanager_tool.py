import io
import urllib.parse
from pathlib import Path
from typing import List, Tuple
from zipfile import ZipFile

import numpy as np
import numpy.typing as npt
from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.study.storage.rawstudy.io.reader.ini_reader import IniReader, MultipleSameKeysIniReader
from antarest.study.storage.variantstudy.model.command.common import CommandName
from antarest.study.storage.variantstudy.model.model import CommandDTO, GenerationResultInfoDTO
from antarest.tools.lib import (
    COMMAND_FILE,
    MATRIX_STORE_DIR,
    RemoteVariantGenerator,
    extract_commands,
    generate_diff,
    generate_study,
    parse_commands,
)

test_dir: Path = Path(__file__).parent


def generate_csv_string(array: npt.NDArray[np.float64]) -> str:
    buffer = io.StringIO()
    np.savetxt(buffer, array, delimiter="\t", fmt="%.6f")
    return buffer.getvalue()


def generate_study_with_server(
    client: TestClient,
    name: str,
    study_version: str,
    commands: List[CommandDTO],
    matrices_dir: Path,
) -> Tuple[GenerationResultInfoDTO, str]:
    res = client.post("/v1/login", json={"username": "admin", "password": "admin"})
    admin_credentials = res.json()
    base_study_res = client.post(
        f"/v1/studies?name=foo&version={study_version}",
        headers={"Authorization": f'Bearer {admin_credentials["access_token"]}'},
    )
    base_study_id = base_study_res.json()
    res = client.post(
        f"/v1/studies/{base_study_id}/variants?name={urllib.parse.quote_plus(name)}",
        headers={"Authorization": f'Bearer {admin_credentials["access_token"]}'},
    )
    variant_id = res.json()
    assert res.status_code == 200
    generator = RemoteVariantGenerator(variant_id, session=client, token=admin_credentials["access_token"])
    return generator.apply_commands(commands, matrices_dir), variant_id


def test_variant_manager(app: FastAPI, tmp_path: str) -> None:
    client = TestClient(app, raise_server_exceptions=False)
    commands = parse_commands(test_dir / "assets" / "commands1.json")
    matrix_dir = Path(tmp_path) / "empty_matrix_store"
    matrix_dir.mkdir(parents=True, exist_ok=True)
    res, study_id = generate_study_with_server(client, "test", "720", commands, matrix_dir)
    assert res is not None and res.success


def test_parse_commands(tmp_path: str, app: FastAPI) -> None:
    base_dir = test_dir / "assets"
    export_path = Path(tmp_path) / "commands"
    study = "base_study"
    study_path = Path(tmp_path) / study
    with ZipFile(base_dir / "base_study.zip") as zip_output:
        zip_output.extractall(path=tmp_path)
    output_dir = Path(export_path) / study
    study_info = IniReader().read(study_path / "study.antares")
    version = study_info["antares"]["version"]
    name = study_info["antares"]["caption"]
    client = TestClient(app, raise_server_exceptions=False)

    extract_commands(study_path, output_dir)
    commands = [CommandDTO(action=CommandName.REMOVE_DISTRICT.value, args={"id": "all areas"})] + parse_commands(
        output_dir / COMMAND_FILE
    )
    res, study_id = generate_study_with_server(client, name, version, commands, output_dir / MATRIX_STORE_DIR)
    assert res is not None and res.success
    generated_study_path = Path(tmp_path) / "internal_workspace" / study_id / "snapshot"
    assert generated_study_path.exists() and generated_study_path.is_dir()

    single_column_empty_items = [
        "input/load/series/load_hub w.txt",
        "input/load/series/load_south.txt",
        "input/load/series/load_hub n.txt",
        "input/load/series/load_west.txt",
        "input/load/series/load_north.txt",
        "input/load/series/load_hub s.txt",
        "input/load/series/load_hub e.txt",
        "input/load/series/load_east.txt",
        "input/wind/series/wind_east.txt",
        "input/wind/series/wind_north.txt",
        "input/wind/series/wind_hub n.txt",
        "input/wind/series/wind_south.txt",
        "input/wind/series/wind_hub w.txt",
        "input/wind/series/wind_west.txt",
        "input/wind/series/wind_hub e.txt",
        "input/wind/series/wind_hub s.txt",
        "input/solar/series/solar_east.txt",
        "input/solar/series/solar_hub n.txt",
        "input/solar/series/solar_south.txt",
        "input/solar/series/solar_hub s.txt",
        "input/solar/series/solar_north.txt",
        "input/solar/series/solar_hub w.txt",
        "input/solar/series/solar_hub e.txt",
        "input/solar/series/solar_west.txt",
        "input/thermal/series/west/semi base/series.txt",
        "input/thermal/series/west/peak/series.txt",
        "input/thermal/series/west/base/series.txt",
        "input/thermal/series/north/semi base/series.txt",
        "input/thermal/series/north/peak/series.txt",
        "input/thermal/series/north/base/series.txt",
        "input/thermal/series/east/semi base/series.txt",
        "input/thermal/series/east/peak/series.txt",
        "input/thermal/series/east/base/series.txt",
        "input/thermal/series/south/semi base/series.txt",
        "input/thermal/series/south/peak/series.txt",
        "input/thermal/series/south/base/series.txt",
        "input/hydro/series/hub e/ror.txt",
        "input/hydro/series/south/ror.txt",
        "input/hydro/series/hub w/ror.txt",
        "input/hydro/series/hub s/ror.txt",
        "input/hydro/series/west/ror.txt",
        "input/hydro/series/hub n/ror.txt",
        "input/hydro/series/north/ror.txt",
        "input/hydro/series/east/ror.txt",
    ]
    single_column_daily_empty_items = [
        "input/hydro/series/hub e/mod.txt",
        "input/hydro/series/south/mod.txt",
        "input/hydro/series/hub w/mod.txt",
        "input/hydro/series/hub s/mod.txt",
        "input/hydro/series/west/mod.txt",
        "input/hydro/series/hub n/mod.txt",
        "input/hydro/series/north/mod.txt",
        "input/hydro/series/east/mod.txt",
    ]
    fixed_3_cols_hourly_empty_items = [
        "input/bindingconstraints/northern mesh.txt",
        "input/bindingconstraints/southern mesh.txt",
    ]
    fixed_4_cols_empty_items = [
        "input/reserves/hub s.txt",
        "input/reserves/hub n.txt",
        "input/reserves/hub w.txt",
        "input/reserves/hub e.txt",
    ]
    fixed_8_cols_empty_items = [
        "input/misc-gen/miscgen-hub w.txt",
        "input/misc-gen/miscgen-hub e.txt",
        "input/misc-gen/miscgen-hub s.txt",
        "input/misc-gen/miscgen-hub n.txt",
    ]
    single_column_empty_data = generate_csv_string(np.zeros((8760, 1), dtype=np.float64))
    single_column_daily_empty_data = generate_csv_string(np.zeros((365, 1), dtype=np.float64))
    fixed_3_cols_hourly_empty_data = generate_csv_string(np.zeros(shape=(8760, 3), dtype=np.float64))
    fixed_4_columns_empty_data = generate_csv_string(np.zeros((8760, 4), dtype=np.float64))
    fixed_8_columns_empty_data = generate_csv_string(np.zeros((8760, 8), dtype=np.float64))
    for file_path in study_path.rglob("*"):
        if file_path.is_dir() or file_path.name in ["comments.txt", "study.antares", "Desktop.ini", "study.ico"]:
            continue
        item_relpath = file_path.relative_to(study_path).as_posix()
        if item_relpath in single_column_empty_items:
            assert (generated_study_path / item_relpath).read_text() == single_column_empty_data
        elif item_relpath in single_column_daily_empty_items:
            assert (generated_study_path / item_relpath).read_text() == single_column_daily_empty_data
        elif item_relpath in fixed_3_cols_hourly_empty_items:
            assert (generated_study_path / item_relpath).read_text() == fixed_3_cols_hourly_empty_data
        elif item_relpath in fixed_4_cols_empty_items:
            assert (generated_study_path / item_relpath).read_text() == fixed_4_columns_empty_data
        elif item_relpath in fixed_8_cols_empty_items:
            assert (generated_study_path / item_relpath).read_text() == fixed_8_columns_empty_data
        elif file_path.suffix == ".ini":
            actual = MultipleSameKeysIniReader().read(study_path / item_relpath)
            expected = MultipleSameKeysIniReader().read(generated_study_path / item_relpath)
            assert actual == expected, f"Invalid configuration: '{item_relpath}'"
        else:
            actual = (study_path / item_relpath).read_text()
            expected = (generated_study_path / item_relpath).read_text()
            assert actual.strip() == expected.strip()


def test_diff_local(tmp_path: Path) -> None:
    base_dir = test_dir / "assets"
    export_path = Path(tmp_path) / "generation_result"
    base_study = "base_study"
    variant_study = "variant_study"
    output_study_commands = export_path / "output_study_commands"
    output_study_path = Path(tmp_path) / base_study
    base_study_commands = export_path / base_study
    variant_study_commands = export_path / variant_study
    variant_study_path = Path(tmp_path) / variant_study

    for study in [base_study, variant_study]:
        with ZipFile(base_dir / f"{study}.zip") as zip_output:
            zip_output.extractall(path=tmp_path)
        extract_commands(Path(tmp_path) / study, export_path / study)

    generate_study(base_study_commands, None, str(export_path / "base_generated"))
    generate_study(
        variant_study_commands,
        None,
        str(export_path / "variant_generated"),
    )
    generate_diff(base_study_commands, variant_study_commands, output_study_commands)
    res = generate_study(output_study_commands, None, output=str(output_study_path))
    assert res.success

    assert output_study_path.exists() and output_study_path.is_dir()
    for file_path in variant_study_path.rglob("*"):
        if file_path.is_dir() or file_path.name in ["comments.txt", "study.antares", "Desktop.ini", "study.ico"]:
            continue
        item_relpath = file_path.relative_to(variant_study_path).as_posix()
        if file_path.suffix == ".ini":
            actual = MultipleSameKeysIniReader().read(variant_study_path / item_relpath)
            expected = MultipleSameKeysIniReader().read(output_study_path / item_relpath)
            assert actual == expected, f"Invalid configuration: '{item_relpath}'"
        else:
            actual = (variant_study_path / item_relpath).read_text()
            expected = (output_study_path / item_relpath).read_text()
            assert actual.strip() == expected.strip()
