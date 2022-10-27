import logging
import os
import urllib.parse
from pathlib import Path
from typing import Optional, List, Tuple
from zipfile import ZipFile

from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.study.storage.rawstudy.io.reader import IniReader
from antarest.study.storage.rawstudy.model.filesystem.matrix.constants import (
    default_scenario_hourly,
    default_4_fixed_hourly,
    default_8_fixed_hourly,
)
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.remove_district import (
    RemoveDistrict,
)
from antarest.study.storage.variantstudy.model.model import (
    CommandDTO,
    GenerationResultInfoDTO,
)
from antarest.tools.lib import (
    COMMAND_FILE,
    MATRIX_STORE_DIR,
    parse_commands,
    extract_commands,
    RemoteVariantGenerator,
    generate_diff,
    generate_study,
)

test_dir: Path = Path(__file__).parent


def generate_csv_string(data: List[List[float]]) -> str:
    csv_str = ""
    for row in data:
        csv_str += "\t".join(["{:.6f}".format(v) for v in row]) + "\n"
    return csv_str


def generate_study_with_server(
    client: TestClient,
    name: str,
    study_version: str,
    commands: List[CommandDTO],
    matrices_dir: Path,
) -> Tuple[GenerationResultInfoDTO, str]:
    res = client.post(
        "/v1/login", json={"username": "admin", "password": "admin"}
    )
    admin_credentials = res.json()
    base_study_res = client.post(
        f"/v1/studies?name=foo&version={study_version}",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    base_study_id = base_study_res.json()
    res = client.post(
        f"/v1/studies/{base_study_id}/variants?name={urllib.parse.quote_plus(name)}",
        headers={
            "Authorization": f'Bearer {admin_credentials["access_token"]}'
        },
    )
    variant_id = res.json()
    assert res.status_code == 200
    generator = RemoteVariantGenerator(
        variant_id, session=client, token=admin_credentials["access_token"]
    )
    return generator.apply_commands(commands, matrices_dir), variant_id


def test_variant_manager(app: FastAPI, tmp_path: str):
    client = TestClient(app, raise_server_exceptions=False)
    commands = parse_commands(test_dir / "assets" / "commands1.json")
    matrix_dir = Path(tmp_path) / "empty_matrix_store"
    matrix_dir.mkdir(parents=True, exist_ok=True)
    res, study_id = generate_study_with_server(
        client, "test", "720", commands, matrix_dir
    )
    assert res is not None and res.success


def test_parse_commands(tmp_path: str, app: FastAPI):
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
    commands = [
        CommandDTO(
            action=CommandName.REMOVE_DISTRICT.value, args={"id": "all areas"}
        )
    ] + parse_commands(output_dir / COMMAND_FILE)
    res, study_id = generate_study_with_server(
        client, name, version, commands, output_dir / MATRIX_STORE_DIR
    )
    assert res is not None and res.success
    generated_study_path = (
        Path(tmp_path) / "internal_workspace" / study_id / "snapshot"
    )
    assert generated_study_path.exists() and generated_study_path.is_dir()

    single_column_empty_items = [
        f"input{os.sep}load{os.sep}series{os.sep}load_hub w.txt",
        f"input{os.sep}load{os.sep}series{os.sep}load_south.txt",
        f"input{os.sep}load{os.sep}series{os.sep}load_hub n.txt",
        f"input{os.sep}load{os.sep}series{os.sep}load_west.txt",
        f"input{os.sep}load{os.sep}series{os.sep}load_north.txt",
        f"input{os.sep}load{os.sep}series{os.sep}load_hub s.txt",
        f"input{os.sep}load{os.sep}series{os.sep}load_hub e.txt",
        f"input{os.sep}load{os.sep}series{os.sep}load_east.txt",
        f"input{os.sep}wind{os.sep}series{os.sep}wind_east.txt",
        f"input{os.sep}wind{os.sep}series{os.sep}wind_north.txt",
        f"input{os.sep}wind{os.sep}series{os.sep}wind_hub n.txt",
        f"input{os.sep}wind{os.sep}series{os.sep}wind_south.txt",
        f"input{os.sep}wind{os.sep}series{os.sep}wind_hub w.txt",
        f"input{os.sep}wind{os.sep}series{os.sep}wind_west.txt",
        f"input{os.sep}wind{os.sep}series{os.sep}wind_hub e.txt",
        f"input{os.sep}wind{os.sep}series{os.sep}wind_hub s.txt",
        f"input{os.sep}solar{os.sep}series{os.sep}solar_east.txt",
        f"input{os.sep}solar{os.sep}series{os.sep}solar_hub n.txt",
        f"input{os.sep}solar{os.sep}series{os.sep}solar_south.txt",
        f"input{os.sep}solar{os.sep}series{os.sep}solar_hub s.txt",
        f"input{os.sep}solar{os.sep}series{os.sep}solar_north.txt",
        f"input{os.sep}solar{os.sep}series{os.sep}solar_hub w.txt",
        f"input{os.sep}solar{os.sep}series{os.sep}solar_hub e.txt",
        f"input{os.sep}solar{os.sep}series{os.sep}solar_west.txt",
        f"input{os.sep}thermal{os.sep}series{os.sep}west{os.sep}semi base{os.sep}series.txt",
        f"input{os.sep}thermal{os.sep}series{os.sep}west{os.sep}peak{os.sep}series.txt",
        f"input{os.sep}thermal{os.sep}series{os.sep}west{os.sep}base{os.sep}series.txt",
        f"input{os.sep}thermal{os.sep}series{os.sep}north{os.sep}semi base{os.sep}series.txt",
        f"input{os.sep}thermal{os.sep}series{os.sep}north{os.sep}peak{os.sep}series.txt",
        f"input{os.sep}thermal{os.sep}series{os.sep}north{os.sep}base{os.sep}series.txt",
        f"input{os.sep}thermal{os.sep}series{os.sep}east{os.sep}semi base{os.sep}series.txt",
        f"input{os.sep}thermal{os.sep}series{os.sep}east{os.sep}peak{os.sep}series.txt",
        f"input{os.sep}thermal{os.sep}series{os.sep}east{os.sep}base{os.sep}series.txt",
        f"input{os.sep}thermal{os.sep}series{os.sep}south{os.sep}semi base{os.sep}series.txt",
        f"input{os.sep}thermal{os.sep}series{os.sep}south{os.sep}peak{os.sep}series.txt",
        f"input{os.sep}thermal{os.sep}series{os.sep}south{os.sep}base{os.sep}series.txt",
    ]
    fixed_4_cols_empty_items = [
        f"input{os.sep}reserves{os.sep}hub s.txt",
        f"input{os.sep}reserves{os.sep}hub n.txt",
        f"input{os.sep}reserves{os.sep}hub w.txt",
        f"input{os.sep}reserves{os.sep}hub e.txt",
    ]
    fixed_8_cols_empty_items = [
        f"input{os.sep}misc-gen{os.sep}miscgen-hub w.txt",
        f"input{os.sep}misc-gen{os.sep}miscgen-hub e.txt",
        f"input{os.sep}misc-gen{os.sep}miscgen-hub s.txt",
        f"input{os.sep}misc-gen{os.sep}miscgen-hub n.txt",
    ]
    single_column_empty_data = generate_csv_string(default_scenario_hourly)
    fixed_4_columns_empty_data = generate_csv_string(default_4_fixed_hourly)
    fixed_8_columns_empty_data = generate_csv_string(default_8_fixed_hourly)
    for root, dirs, files in os.walk(study_path):
        rel_path = root[len(str(study_path)) + 1 :]
        for item in files:
            if item in [
                "comments.txt",
                "study.antares",
                "Desktop.ini",
                "study.ico",
            ]:
                continue
            elif f"{rel_path}{os.sep}{item}" in single_column_empty_items:
                assert (
                    generated_study_path / rel_path / item
                ).read_text() == single_column_empty_data
            elif f"{rel_path}{os.sep}{item}" in fixed_4_cols_empty_items:
                assert (
                    generated_study_path / rel_path / item
                ).read_text() == fixed_4_columns_empty_data
            elif f"{rel_path}{os.sep}{item}" in fixed_8_cols_empty_items:
                assert (
                    generated_study_path / rel_path / item
                ).read_text() == fixed_8_columns_empty_data
            else:
                assert (study_path / rel_path / item).read_text() == (
                    generated_study_path / rel_path / item
                ).read_text()


def test_diff_local(tmp_path: Path):
    base_dir = test_dir / "assets"
    export_path = Path(tmp_path) / "generation_result"
    base_study = "base_study"
    variant_study = "variant_study"
    output_study_commands = Path(export_path) / "output_study_commands"
    output_study_path = Path(tmp_path) / base_study
    base_study_commands = Path(export_path) / base_study
    variant_study_commands = Path(export_path) / variant_study
    variant_study_path = Path(tmp_path) / variant_study

    for study in [base_study, variant_study]:
        with ZipFile(base_dir / f"{study}.zip") as zip_output:
            zip_output.extractall(path=tmp_path)
        extract_commands(Path(tmp_path) / study, Path(export_path) / study)

    res = generate_study(
        base_study_commands, None, str(Path(export_path) / "base_generated")
    )
    res = generate_study(
        variant_study_commands,
        None,
        str(Path(export_path) / "variant_generated"),
    )
    generate_diff(
        base_study_commands, variant_study_commands, output_study_commands
    )
    res = generate_study(
        output_study_commands, None, output=str(output_study_path)
    )
    assert res.success

    assert output_study_path.exists() and output_study_path.is_dir()
    for root, dirs, files in os.walk(variant_study_path):
        rel_path = root[len(str(variant_study_path)) + 1 :]
        for item in files:
            if item in [
                "comments.txt",
                "study.antares",
                "Desktop.ini",
                "study.ico",
            ]:
                continue
            assert (variant_study_path / rel_path / item).read_text() == (
                output_study_path / rel_path / item
            ).read_text()
