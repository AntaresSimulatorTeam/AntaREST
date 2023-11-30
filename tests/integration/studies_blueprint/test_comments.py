import io
import time
from xml.etree import ElementTree

from starlette.testclient import TestClient

from tests.integration.studies_blueprint.assets import ASSETS_DIR
from tests.xml_compare import compare_elements


class TestStudyComments:
    """
    This class contains tests related to the following endpoints:

    - GET /v1/studies/{study_id}/comments
    - PUT /v1/studies/{study_id}/comments
    """

    def test_raw_study(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
    ) -> None:
        """
        This test verifies that we can retrieve and modify the comments of a study.
        It also performs performance measurements and analyzes.
        """

        # Get the comments of the study and compare with the expected file
        res = client.get(
            f"/v1/studies/{study_id}/comments",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        actual_xml = ElementTree.parse(io.StringIO(actual)).getroot()
        expected_xml = ElementTree.parse(ASSETS_DIR.joinpath("test_comments/raw_study.comments.xml")).getroot()
        assert compare_elements(actual_xml, expected_xml) == ""

        # Ensure the duration is relatively short
        start = time.time()
        res = client.get(
            f"/v1/studies/{study_id}/comments",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        duration = time.time() - start
        assert 0 <= duration <= 0.1, f"Duration is {duration} seconds"

        # Update the comments of the study
        res = client.put(
            f"/v1/studies/{study_id}/comments",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"comments": "<text>Ceci est un commentaire en français.</text>"},
        )
        assert res.status_code == 204, res.json()

        # Get the comments of the study and compare with the expected file
        res = client.get(
            f"/v1/studies/{study_id}/comments",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        assert res.json() == "<text>Ceci est un commentaire en français.</text>"

    def test_variant_study(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
    ) -> None:
        """
        This test verifies that we can retrieve and modify the comments of a VARIANT study.
        It also performs performance measurements and analyzes.
        """
        # First, we create a copy of the study, and we convert it to a managed study.
        res = client.post(
            f"/v1/studies/{study_id}/copy",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"dest": "default", "with_outputs": False, "use_task": False},  # type: ignore
        )
        assert res.status_code == 201, res.json()
        base_study_id = res.json()
        assert base_study_id is not None

        # Then, we create a new variant of the base study
        res = client.post(
            f"/v1/studies/{base_study_id}/variants",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"name": f"Variant XYZ"},
        )
        assert res.status_code == 200, res.json()  # should be CREATED
        variant_id = res.json()
        assert variant_id is not None

        # Get the comments of the study and compare with the expected file
        res = client.get(
            f"/v1/studies/{variant_id}/comments",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        actual_xml = ElementTree.parse(io.StringIO(actual)).getroot()
        expected_xml = ElementTree.parse(ASSETS_DIR.joinpath("test_comments/raw_study.comments.xml")).getroot()
        assert compare_elements(actual_xml, expected_xml) == ""

        # Ensure the duration is relatively short
        start = time.time()
        res = client.get(
            f"/v1/studies/{variant_id}/comments",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        duration = time.time() - start
        assert 0 <= duration <= 0.1, f"Duration is {duration} seconds"

        # Update the comments of the study
        res = client.put(
            f"/v1/studies/{variant_id}/comments",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"comments": "<text>Ceci est un commentaire en français.</text>"},
        )
        assert res.status_code == 204, res.json()

        # Get the comments of the study and compare with the expected file
        res = client.get(
            f"/v1/studies/{variant_id}/comments",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        assert res.json() == "<text>Ceci est un commentaire en français.</text>"
