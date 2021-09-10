from pathlib import Path

from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.tools.lib import CLIVariantManager

test_dir: Path = Path(__file__).parent


def test_variant_manager(app: FastAPI):
    client = TestClient(app, raise_server_exceptions=False)

    res = client.post(
        "/v1/login", json={"username": "admin", "password": "admin"}
    )
    admin_credentials = res.json()

    base_study_res = client.post(
        "/v1/studies?name=foo",
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

    commands = vm.parse_commands(test_dir / "assets" / "commands1.json")

    res = vm.apply_commands(variant_id, commands)
    assert res is not None and res.success
