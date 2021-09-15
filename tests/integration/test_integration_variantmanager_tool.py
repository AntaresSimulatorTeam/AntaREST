import logging
import os
import urllib.parse
from pathlib import Path
from typing import Optional, List

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
) -> GenerationResultInfoDTO:
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
    return vm.apply_commands(variant_id, commands, matrices_dir)


def test_variant_manager(app: FastAPI):
    client = TestClient(app, raise_server_exceptions=False)
    res = client.post(
        "/v1/login", json={"username": "admin", "password": "admin"}
    )
    admin_credentials = res.json()
    vm = CLIVariantManager(
        session=client, token=admin_credentials["access_token"]
    )
    commands = vm.parse_commands(test_dir / "assets" / "commands1.json")
    res = generate_study(client, "test", 720, commands)
    assert res is not None and res.success


logger = logging.getLogger(__name__)


def test_parse_commands(tmp_path: str, app: FastAPI):
    # todo add a quite feature-exhaustive test study
    base_dir = Path("/home/buiquangpau/scratch/test_antares_vm")
    export_path = Path(tmp_path) / "commands"
    for study in os.listdir(base_dir):
        study_path = base_dir / study
        output_dir = Path(export_path) / study
        logger.error(study_path)
        logger.error(output_dir)
        try:
            study_info = IniReader().read(study_path / "study.antares")
            version = study_info["antares"]["version"]
            name = study_info["antares"]["caption"]
            client = TestClient(app, raise_server_exceptions=False)
            res = client.post(
                "/v1/login", json={"username": "admin", "password": "admin"}
            )
            admin_credentials = res.json()
            vm = CLIVariantManager(
                session=client, token=admin_credentials["access_token"]
            )

            CLIVariantManager.extract_commands(study_path, output_dir)
            commands = vm.parse_commands(output_dir / "commands.json")
            res = generate_study(
                client, name, version, commands, output_dir / "matrices"
            )
            logger.error(res.json())
            break
            #        assert res is not None and res.success
        except Exception as e:
            logger.error(f"Failure on {study_path}", exc_info=e)
