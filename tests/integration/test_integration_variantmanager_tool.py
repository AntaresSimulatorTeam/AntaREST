from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.study.storage.variantstudy.model.model import (
    CommandDTO,
    GenerationResultInfoDTO,
)
from antarest.tools.lib import CLIVariantManager

test_dir: Path = Path(__file__).parent


def generate_study(
    client: TestClient,
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
        f"/v1/studies/{base_study_id}/variants?name=foo",
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
    res = generate_study(client, 720, commands)
    assert res is not None and res.success


def test_parse_commands(tmp_path: str, app: FastAPI):
    # todo add a quite feature-exhaustive test study
    # study_path = Path(
    # )
    # output_dir = Path(tmp_path)
    # CLIVariantManager.extract_commands(study_path, output_dir)
    #
    # client = TestClient(app, raise_server_exceptions=False)
    # res = client.post(
    #     "/v1/login", json={"username": "admin", "password": "admin"}
    # )
    # admin_credentials = res.json()
    # vm = CLIVariantManager(
    #     session=client, token=admin_credentials["access_token"]
    # )
    # commands = vm.parse_commands(output_dir / "commands.json")
    # res = generate_study(client, 700, commands, output_dir / "matrices")
    # assert res is not None and res.success
    pass
