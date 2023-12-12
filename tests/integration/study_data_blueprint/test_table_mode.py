import re

import numpy as np
import pytest
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from antarest.study.storage.rawstudy.model.filesystem.config.model import transform_name_to_id
from tests.integration.utils import wait_task_completion


@pytest.mark.unit_test
class TestTableMode:
    """
    Test the end points related to the table mode.

    Those tests use the "examples/studies/STA-mini.zip" Study,
    which contains the following areas: ["de", "es", "fr", "it"].
    """

    def test_lifecycle__nominal(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
    ) -> None:
        # we are working with the "DE" area
        area_id = "de"
        user_headers = {"Authorization": f"Bearer {user_access_token}"}

        # Table Mode - Area
        res = client.get(
            f"/v1/studies/{study_id}/tablemode/form",
            headers=user_headers,
            params={
                "table_type": "area",
                "columns": ",".join(["nonDispatchablePower", "dispatchableHydroPower", "otherDispatchablePower"]),
            },
        )
        assert res.status_code == 200, res.json()
        expected = {
            "de": {
                "dispatchableHydroPower": True,
                "nonDispatchablePower": True,
                "otherDispatchablePower": True,
            },
            "es": {
                "dispatchableHydroPower": True,
                "nonDispatchablePower": True,
                "otherDispatchablePower": True,
            },
            "fr": {
                "dispatchableHydroPower": True,
                "nonDispatchablePower": True,
                "otherDispatchablePower": True,
            },
            "it": {
                "dispatchableHydroPower": True,
                "nonDispatchablePower": True,
                "otherDispatchablePower": True,
            },
        }
        actual = res.json()
        assert actual == expected
