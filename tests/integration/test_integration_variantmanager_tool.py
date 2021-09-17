import logging
import os
import urllib.parse
from pathlib import Path
from typing import Optional, List, Tuple
from zipfile import ZipFile

from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.study.storage.rawstudy.io.reader import IniReader
from antarest.study.storage.variantstudy.model.model import (
    CommandDTO,
    GenerationResultInfoDTO,
)
from antarest.tools.lib import CLIVariantManager

test_dir: Path = Path(__file__).parent


def generate_study(
    client: TestClient,
    name: str,
    study_version: int,
    commands: List[CommandDTO],
    matrices_dir: Optional[Path] = None,
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
    vm = CLIVariantManager(
        session=client, token=admin_credentials["access_token"]
    )
    return vm.apply_commands(variant_id, commands, matrices_dir), variant_id


def test_variant_manager(app: FastAPI):
    client = TestClient(app, raise_server_exceptions=False)
    commands = CLIVariantManager.parse_commands(
        test_dir / "assets" / "commands1.json"
    )
    res, study_id = generate_study(client, "test", 720, commands)
    assert res is not None and res.success


def test_parse_commands(tmp_path: str, app: FastAPI):
    base_dir = test_dir / "assets"
    export_path = Path(tmp_path) / "commands"
    study = "test_study"
    study_path = Path(tmp_path) / study
    with ZipFile(base_dir / "test_study.zip") as zip_output:
        zip_output.extractall(path=tmp_path)
    output_dir = Path(export_path) / study
    study_info = IniReader().read(study_path / "study.antares")
    version = study_info["antares"]["version"]
    name = study_info["antares"]["caption"]
    client = TestClient(app, raise_server_exceptions=False)

    CLIVariantManager.extract_commands(study_path, output_dir)
    commands = CLIVariantManager.parse_commands(output_dir / "commands.json")
    res, study_id = generate_study(
        client, name, version, commands, output_dir / "matrices"
    )
    assert res is not None and res.success
    generated_study_path = (
        Path(tmp_path) / "internal_workspace" / study_id / "snapshot"
    )
    assert generated_study_path.exists() and generated_study_path.is_dir()
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
            print(generated_study_path / rel_path / item)
            assert (study_path / rel_path / item).read_text() == (
                generated_study_path / rel_path / item
            ).read_text()
