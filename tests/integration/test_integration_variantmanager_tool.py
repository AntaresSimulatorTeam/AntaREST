import os
import urllib.parse
import zipfile
from pathlib import Path
from typing import List, Tuple

import numpy as np
from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.study.storage.rawstudy.io.reader import IniReader
from antarest.study.storage.rawstudy.model.filesystem.matrix.constants import (
    default_4_fixed_hourly,
    default_8_fixed_hourly,
    default_scenario_daily,
    default_scenario_hourly,
)
from antarest.study.storage.study_upgrader import get_current_version
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
)
from antarest.study.storage.variantstudy.model.model import (
    CommandDTO,
    GenerationResultInfoDTO,
)
from antarest.tools.lib import (
    COMMAND_FILE,
    MATRIX_STORE_DIR,
    RemoteVariantGenerator,
    extract_commands,
    generate_diff,
    generate_study,
    parse_commands,
)

TEST_DIR: Path = Path(__file__).parent


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
    commands = parse_commands(TEST_DIR / "assets" / "commands1.json")
    matrix_dir = Path(tmp_path) / "empty_matrix_store"
    matrix_dir.mkdir(parents=True, exist_ok=True)
    res, study_id = generate_study_with_server(
        client, "test", "720", commands, matrix_dir
    )
    assert res is not None and res.success


def test_parse_commands(tmp_path: str, app: FastAPI):
    base_dir = TEST_DIR / "assets"
    export_path = Path(tmp_path) / "commands"
    study = "base_study"
    study_path = Path(tmp_path) / study
    with zipfile.ZipFile(base_dir / "base_study.zip") as zip_output:
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
    fixed_4_cols_empty_items = [
        "input/reserves/hub s.txt",
        "input/reserves/hub n.txt",
        "input/reserves/hub w.txt",
        "input/reserves/hub e.txt",
    ]
    # noinspection SpellCheckingInspection
    fixed_8_cols_empty_items = [
        "input/misc-gen/miscgen-hub w.txt",
        "input/misc-gen/miscgen-hub e.txt",
        "input/misc-gen/miscgen-hub s.txt",
        "input/misc-gen/miscgen-hub n.txt",
    ]
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
            elif f"{rel_path}/{item}" in single_column_empty_items:
                assert (
                    np.loadtxt(generated_study_path / rel_path / item)
                    == default_scenario_hourly
                ).all()
            elif f"{rel_path}/{item}" in single_column_daily_empty_items:
                assert (
                    np.loadtxt(generated_study_path / rel_path / item)
                    == default_scenario_daily
                ).all()
            elif f"{rel_path}/{item}" in fixed_4_cols_empty_items:
                assert (
                    np.loadtxt(generated_study_path / rel_path / item)
                    == default_4_fixed_hourly
                ).all()
            elif f"{rel_path}/{item}" in fixed_8_cols_empty_items:
                assert (
                    np.loadtxt(generated_study_path / rel_path / item)
                    == default_8_fixed_hourly
                ).all()
            else:
                assert (study_path / rel_path / item).read_text() == (
                    generated_study_path / rel_path / item
                ).read_text()


def test_diff_local(tmp_path: Path):
    # Extract resources in `assets`
    assets_dir = tmp_path.joinpath("assets")
    assets_dir.mkdir()
    raw_study_dir = assets_dir.joinpath("raw_study")
    variant_study_dir = assets_dir.joinpath("variant_study")
    for src in [
        TEST_DIR.joinpath("assets/base_study.zip"),
        TEST_DIR.joinpath("assets/variant_study.zip"),
    ]:
        with zipfile.ZipFile(src) as zip_output:
            zip_output.extractall(path=assets_dir)
    assets_dir.joinpath("base_study").replace(raw_study_dir)

    # Extract the commands used to "regenerate" the studies
    results_dir = tmp_path.joinpath("results")
    commands_dir = results_dir.joinpath("commands")
    raw_study_commands = commands_dir.joinpath("raw_study")
    variant_study_commands = commands_dir.joinpath("variant_study")
    extract_commands(raw_study_dir, raw_study_commands)
    extract_commands(variant_study_dir, variant_study_commands),

    study_version = get_current_version(raw_study_dir)

    raw_generated_dir = results_dir.joinpath("raw_generated")
    res = generate_study(
        raw_study_commands,
        "raw1",
        output=str(raw_generated_dir),
        study_version=study_version,
    )
    assert res.success
    variant_generated_dir = results_dir.joinpath("variant_generated")
    res = generate_study(
        variant_study_commands,
        "variant1",
        output=str(variant_generated_dir),
        study_version=study_version,
    )
    assert res.success
    # Calculates the differences between the RAW study and the variant study.
    generate_diff(
        raw_study_commands,
        variant_study_commands,
        commands_dir,
        study_version=study_version,
    )
    # After calculating the differences, the `generate_diff` function generates a list
    # of commands that only contains the differences between the two studies.
    # These differences are then applied to the original RAW study to regenerate
    # a study in the final state.
    res = generate_study(
        commands_dir,
        "diff1",
        output=str(raw_generated_dir),
        study_version=study_version,
    )
    assert res.success

    # Quick compare generated raw and variant
    for raw_path in raw_generated_dir.glob("**/*"):
        if raw_path.is_dir() or raw_path.name in [
            "comments.txt",
            "study.antares",
            "Desktop.ini",
            "study.ico",
        ]:
            continue
        relpath = raw_path.relative_to(raw_generated_dir)
        variant_path = variant_generated_dir.joinpath(relpath)
        raw_text = raw_path.read_text(encoding="utf-8")
        variant_text = variant_path.read_text(encoding="utf-8")
        assert raw_text == variant_text, f"Invalid path '{relpath}'"
