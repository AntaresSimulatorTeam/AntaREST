import io
import re

import numpy as np
import pandas as pd
import pytest
from starlette.testclient import TestClient

from antarest.study.business.binding_constraint_management import ClusterTerm, ConstraintTerm, LinkTerm


class TestLinkTerm:
    @pytest.mark.parametrize(
        "area1, area2, expected",
        [
            ("Area 1", "Area 2", "area 1%area 2"),
            ("de", "fr", "de%fr"),
            ("fr", "de", "de%fr"),
            ("FR", "de", "de%fr"),
        ],
    )
    def test_constraint_id(self, area1: str, area2: str, expected: str) -> None:
        info = LinkTerm(area1=area1, area2=area2)
        assert info.generate_id() == expected


class TestClusterTerm:
    @pytest.mark.parametrize(
        "area, cluster, expected",
        [
            ("Area 1", "Cluster X", "area 1.cluster x"),
            ("de", "Nuclear", "de.nuclear"),
            ("GB", "Gas", "gb.gas"),
        ],
    )
    def test_constraint_id(self, area: str, cluster: str, expected: str) -> None:
        info = ClusterTerm(area=area, cluster=cluster)
        assert info.generate_id() == expected


class TestConstraintTerm:
    def test_constraint_id__link(self) -> None:
        term = ConstraintTerm(
            id="foo",
            weight=3.14,
            offset=123,
            data=LinkTerm(area1="Area 1", area2="Area 2"),
        )
        assert term.generate_id() == term.data.generate_id()

    def test_constraint_id__cluster(self) -> None:
        term = ConstraintTerm(
            id="foo",
            weight=3.14,
            offset=123,
            data=ClusterTerm(area="Area 1", cluster="Cluster X"),
        )
        assert term.generate_id() == term.data.generate_id()

    def test_constraint_id__other(self) -> None:
        term = ConstraintTerm(
            id="foo",
            weight=3.14,
            offset=123,
        )
        assert term.generate_id() == "foo"


def _upload_matrix(
    client: TestClient, user_access_token: str, study_id: str, matrix_path: str, df: pd.DataFrame
) -> None:
    tsv = io.BytesIO()
    df.to_csv(tsv, sep="\t", index=False, header=False)
    tsv.seek(0)
    res = client.put(
        f"/v1/studies/{study_id}/raw",
        params={"path": matrix_path},
        headers={"Authorization": f"Bearer {user_access_token}"},
        files={"file": tsv},
    )
    res.raise_for_status()


@pytest.mark.unit_test
class TestBindingConstraints:
    """
    Test the end points related to binding constraints.
    """

    @pytest.mark.parametrize("study_type", ["raw", "variant"])
    def test_lifecycle__nominal(self, client: TestClient, user_access_token: str, study_type: str) -> None:
        user_headers = {"Authorization": f"Bearer {user_access_token}"}

        # =============================
        #  STUDY PREPARATION
        # =============================

        # Create a Study
        res = client.post(
            "/v1/studies",
            headers=user_headers,
            params={"name": "foo", "version": "860"},
        )
        assert res.status_code == 201, res.json()
        study_id = res.json()

        # Create Areas
        res = client.post(
            f"/v1/studies/{study_id}/areas",
            headers=user_headers,
            json={
                "name": "Area 1",
                "type": "AREA",
            },
        )
        assert res.status_code == 200, res.json()
        area1_id = res.json()["id"]
        assert area1_id == "area 1"

        res = client.post(
            f"/v1/studies/{study_id}/areas",
            headers=user_headers,
            json={
                "name": "Area 2",
                "type": "AREA",
            },
        )
        assert res.status_code == 200, res.json()
        area2_id = res.json()["id"]
        assert area2_id == "area 2"

        # Create a link between the two areas
        res = client.post(
            f"/v1/studies/{study_id}/links",
            headers=user_headers,
            json={
                "area1": area1_id,
                "area2": area2_id,
            },
        )
        assert res.status_code == 200, res.json()

        # Create a cluster in area1
        res = client.post(
            f"/v1/studies/{study_id}/areas/{area1_id}/clusters/thermal",
            headers=user_headers,
            json={
                "name": "Cluster 1",
                "group": "Nuclear",
            },
        )
        assert res.status_code == 200, res.json()
        cluster_id = res.json()["id"]
        assert cluster_id == "Cluster 1"

        # Get clusters list to check created cluster in area1
        res = client.get(f"/v1/studies/{study_id}/areas/{area1_id}/clusters/thermal", headers=user_headers)
        clusters_list = res.json()
        assert res.status_code == 200, res.json()
        assert len(clusters_list) == 1
        assert clusters_list[0]["id"] == cluster_id
        assert clusters_list[0]["name"] == "Cluster 1"
        assert clusters_list[0]["group"] == "Nuclear"

        if study_type == "variant":
            # Create Variant
            res = client.post(
                f"/v1/studies/{study_id}/variants",
                headers=user_headers,
                params={"name": "Variant 1"},
            )
            assert res.status_code in {200, 201}, res.json()
            study_id = res.json()

        # =============================
        # CREATION
        # =============================

        # Create Binding constraints
        res = client.post(
            f"/v1/studies/{study_id}/commands",
            json=[
                {
                    "action": "create_binding_constraint",
                    "args": {
                        "name": "binding_constraint_1",
                        "enabled": True,
                        "time_step": "hourly",
                        "operator": "less",
                        "coeffs": {},
                        "comments": "",
                    },
                }
            ],
            headers=user_headers,
        )
        assert res.status_code in {200, 201}, res.json()

        res = client.post(
            f"/v1/studies/{study_id}/commands",
            json=[
                {
                    "action": "create_binding_constraint",
                    "args": {
                        "name": "binding_constraint_2",
                        "enabled": True,
                        "time_step": "hourly",
                        "operator": "less",
                        "coeffs": {},
                        "comments": "",
                    },
                }
            ],
            headers=user_headers,
        )
        assert res.status_code in {200, 201}, res.json()

        # Creates a binding constraint with the new API
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={
                "name": "binding_constraint_3",
                "enabled": True,
                "timeStep": "hourly",
                "operator": "less",
                "terms": [],
                "comments": "New API",
            },
            headers=user_headers,
        )
        assert res.status_code in {200, 201}, res.json()

        # Get Binding Constraint list
        res = client.get(f"/v1/studies/{study_id}/bindingconstraints", headers=user_headers)
        binding_constraints_list = res.json()
        assert res.status_code == 200, res.json()
        assert len(binding_constraints_list) == 3
        # Group section should not exist as the study version is prior to 8.7
        assert "group" not in binding_constraints_list[0]
        # check whole structure
        expected = [
            {
                "comments": "",
                "terms": [],
                "enabled": True,
                "filterSynthesis": "",
                "filterYearByYear": "",
                "id": "binding_constraint_1",
                "name": "binding_constraint_1",
                "operator": "less",
                "timeStep": "hourly",
            },
            {
                "comments": "",
                "terms": [],
                "enabled": True,
                "filterSynthesis": "",
                "filterYearByYear": "",
                "id": "binding_constraint_2",
                "name": "binding_constraint_2",
                "operator": "less",
                "timeStep": "hourly",
            },
            {
                "comments": "New API",
                "terms": [],
                "enabled": True,
                "filterSynthesis": "",
                "filterYearByYear": "",
                "id": "binding_constraint_3",
                "name": "binding_constraint_3",
                "operator": "less",
                "timeStep": "hourly",
            },
        ]
        assert binding_constraints_list == expected

        bc_id = binding_constraints_list[0]["id"]

        # Asserts binding constraint configuration is valid.
        res = client.get(f"/v1/studies/{study_id}/constraint-groups", headers=user_headers)
        assert res.status_code == 200, res.json()

        # =============================
        # CONSTRAINT TERM MANAGEMENT
        # =============================

        # Add binding constraint link term
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id}/term",
            json={
                "weight": 1,
                "offset": 2,
                "data": {"area1": area1_id, "area2": area2_id},
            },
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()

        # Add binding constraint cluster term
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id}/term",
            json={
                "weight": 1,
                "offset": 2,
                "data": {
                    "area": area1_id,
                    "cluster": cluster_id,
                },
                # NOTE: cluster_id in term data can be uppercase, but it must be lowercase in the returned ini configuration file
            },
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()

        # Get binding constraints list to check added terms
        res = client.get(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id}",
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()
        binding_constraint = res.json()
        constraint_terms = binding_constraint["terms"]
        expected = [
            {
                "data": {"area1": area1_id, "area2": area2_id},
                "id": f"{area1_id}%{area2_id}",
                "offset": 2,
                "weight": 1.0,
            },
            {
                "data": {"area": area1_id, "cluster": cluster_id.lower()},
                "id": f"{area1_id}.{cluster_id.lower()}",
                "offset": 2,
                "weight": 1.0,
            },
        ]
        assert constraint_terms == expected

        # Update constraint cluster term with uppercase cluster_id
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id}/term",
            json={
                "id": f"{area1_id}.{cluster_id}",
                "weight": 3,
            },
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()

        # Check updated terms, cluster_id should be lowercase in the returned configuration
        res = client.get(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id}",
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()
        binding_constraint = res.json()
        constraint_terms = binding_constraint["terms"]
        expected = [
            {
                "data": {"area1": area1_id, "area2": area2_id},
                "id": f"{area1_id}%{area2_id}",
                "offset": 2,
                "weight": 1.0,
            },
            {
                "data": {"area": area1_id, "cluster": cluster_id.lower()},
                "id": f"{area1_id}.{cluster_id.lower()}",
                "offset": None,  # updated
                "weight": 3.0,  # updated
            },
        ]
        assert constraint_terms == expected

        # Update constraint cluster term with invalid id
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id}/term",
            json={
                "id": f"{area1_id}.!!Invalid#cluster%%",
                "weight": 4,
            },
            headers=user_headers,
        )
        assert res.status_code == 404, res.json()
        assert res.json() == {
            "description": f"{study_id}",
            "exception": "ConstraintIdNotFoundError",
        }

        # Update constraint cluster term with empty data
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id}/term",
            json={
                "id": f"{area1_id}.{cluster_id}",
                "data": {},
            },
            headers=user_headers,
        )
        assert res.status_code == 422, res.json()
        assert res.json() == {
            "body": {"data": {}, "id": f"{area1_id}.{cluster_id}"},
            "description": "field required",
            "exception": "RequestValidationError",
        }

        # Remove Constraint term
        res = client.delete(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id}/term/{area1_id}%{area2_id}",
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()

        # Check updated terms, the deleted term should no longer exist.
        res = client.get(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id}",
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()
        binding_constraint = res.json()
        constraint_terms = binding_constraint["terms"]
        expected = [
            {
                "data": {"area": area1_id, "cluster": cluster_id.lower()},
                "id": f"{area1_id}.{cluster_id.lower()}",
                "offset": None,
                "weight": 3.0,
            },
        ]
        assert constraint_terms == expected

        # =============================
        # GENERAL EDITION
        # =============================

        # Update element of Binding constraint
        new_comment = "We made it !"
        res = client.put(
            f"v1/studies/{study_id}/bindingconstraints/{bc_id}",
            json={"comments": new_comment},
            headers=user_headers,
        )
        assert res.status_code == 200
        assert res.json()["comments"] == new_comment

        # The user change the timeStep to daily instead of hourly.
        # We must check that the matrix is a daily/weekly matrix.
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id}",
            json={"timeStep": "daily"},
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()
        assert res.json()["timeStep"] == "daily"

        # Check that the command corresponds to a change in `time_step`
        if study_type == "variant":
            res = client.get(f"/v1/studies/{study_id}/commands", headers=user_headers)
            commands = res.json()
            args = commands[-1]["args"]
            assert args["time_step"] == "daily"
            assert args["values"] is not None, "We should have a matrix ID (sha256)"

        # Check that the matrix is a daily/weekly matrix
        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": f"input/bindingconstraints/{bc_id}", "depth": 1, "formatted": True},  # type: ignore
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()
        dataframe = res.json()
        assert len(dataframe["index"]) == 366
        assert len(dataframe["columns"]) == 3  # less, equal, greater

        # =============================
        # ERRORS
        # =============================

        # Assert empty name
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={
                "name": "  ",
                "enabled": True,
                "timeStep": "hourly",
                "operator": "less",
                "terms": [],
                "comments": "New API",
            },
            headers=user_headers,
        )
        assert res.status_code == 400, res.json()
        assert res.json() == {
            "description": "Invalid binding constraint name:   .",
            "exception": "InvalidConstraintName",
        }

        # Assert invalid special characters
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={
                "name": "%%**",
                "enabled": True,
                "timeStep": "hourly",
                "operator": "less",
                "terms": [],
                "comments": "New API",
            },
            headers=user_headers,
        )
        assert res.status_code == 400, res.json()
        assert res.json() == {
            "description": "Invalid binding constraint name: %%**.",
            "exception": "InvalidConstraintName",
        }

        # Asserts that creating 2 binding constraints with the same name raises an Exception
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={
                "name": bc_id,
                "enabled": True,
                "timeStep": "hourly",
                "operator": "less",
                "terms": [],
                "comments": "",
            },
            headers=user_headers,
        )
        assert res.status_code == 409, res.json()

        # Creation with matrices from 2 versions: Should fail
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={
                "name": "binding_constraint_x",
                "enabled": True,
                "timeStep": "hourly",
                "operator": "less",
                "terms": [],
                "comments": "2 types of matrices",
                "values": [[]],
                "less_term_matrix": [[]],
            },
            headers=user_headers,
        )
        assert res.status_code == 422
        description = res.json()["description"]
        assert "cannot fill 'values'" in description
        assert "'less_term_matrix'" in description
        assert "'greater_term_matrix'" in description
        assert "'equal_term_matrix'" in description

        # Creation with wrong matrix according to version: Should fail
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={
                "name": "binding_constraint_x",
                "enabled": True,
                "timeStep": "hourly",
                "operator": "less",
                "terms": [],
                "comments": "Incoherent matrix with version",
                "less_term_matrix": [[]],
            },
            headers=user_headers,
        )
        assert res.status_code == 422
        description = res.json()["description"]
        assert description == "You cannot fill a 'matrix_term' as these values refer to v8.7+ studies"

        # Wrong matrix shape
        wrong_matrix = np.ones((352, 3))
        wrong_request_args = {
            "name": "binding_constraint_5",
            "enabled": True,
            "timeStep": "daily",
            "operator": "less",
            "terms": [],
            "comments": "Creation with matrix",
            "values": wrong_matrix.tolist(),
        }
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json=wrong_request_args,
            headers=user_headers,
        )
        assert res.status_code == 422, res.json()
        exception = res.json()["exception"]
        description = res.json()["description"]
        assert exception == "RequestValidationError"
        assert "'values'" in description
        assert "(366, 3)" in description

        # Delete a fake binding constraint
        res = client.delete(f"/v1/studies/{study_id}/bindingconstraints/fake_bc", headers=user_headers)
        assert res.status_code == 404, res.json()
        assert res.json()["exception"] == "BindingConstraintNotFoundError"
        assert res.json()["description"] == "Binding constraint 'fake_bc' not found"

        # Add a group before v8.7
        grp_name = "random_grp"
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/binding_constraint_2",
            json={"group": grp_name},
            headers=user_headers,
        )
        assert res.status_code == 422, res.json()
        assert res.json()["exception"] == "InvalidFieldForVersionError"
        assert (
            res.json()["description"]
            == f"You cannot specify a group as your study version is older than v8.7: {grp_name}"
        )

        # Update with a matrix from v8.7
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/binding_constraint_2",
            json={"less_term_matrix": [[]]},
            headers=user_headers,
        )
        assert res.status_code == 422, res.json()
        assert res.json()["exception"] == "InvalidFieldForVersionError"
        assert res.json()["description"] == "You cannot fill a 'matrix_term' as these values refer to v8.7+ studies"

    @pytest.mark.parametrize("study_type", ["raw", "variant"])
    def test_for_version_870(self, client: TestClient, admin_access_token: str, study_type: str) -> None:
        admin_headers = {"Authorization": f"Bearer {admin_access_token}"}

        # =============================
        #  STUDY PREPARATION
        # =============================

        res = client.post(
            "/v1/studies",
            headers=admin_headers,
            params={"name": "foo"},
        )
        assert res.status_code == 201, res.json()
        study_id = res.json()

        if study_type == "variant":
            # Create Variant
            res = client.post(
                f"/v1/studies/{study_id}/variants",
                headers=admin_headers,
                params={"name": "Variant 1"},
            )
            assert res.status_code in {200, 201}
            study_id = res.json()

        # =============================
        #  CREATION
        # =============================

        # Creation of a bc without group
        bc_id_wo_group = "binding_constraint_1"
        args = {"enabled": True, "timeStep": "hourly", "operator": "less", "terms": [], "comments": "New API"}
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={"name": bc_id_wo_group, **args},
            headers=admin_headers,
        )
        assert res.status_code in {200, 201}
        assert res.json()["group"] == "default"

        # Creation of bc with a group
        bc_id_w_group = "binding_constraint_2"
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={"name": bc_id_w_group, "group": "specific_grp", **args},
            headers=admin_headers,
        )
        assert res.status_code in {200, 201}
        assert res.json()["group"] == "specific_grp"

        # Creation of bc with a matrix
        bc_id_w_matrix = "binding_constraint_3"
        matrix_lt3 = np.ones((8784, 3))
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={"name": bc_id_w_matrix, "less_term_matrix": matrix_lt3.tolist(), **args},
            headers=admin_headers,
        )
        assert res.status_code in {200, 201}, res.json()

        if study_type == "variant":
            res = client.get(f"/v1/studies/{study_id}/commands", headers=admin_headers)
            last_cmd_args = res.json()[-1]["args"]
            less_term_matrix = last_cmd_args["less_term_matrix"]
            equal_term_matrix = last_cmd_args["equal_term_matrix"]
            greater_term_matrix = last_cmd_args["greater_term_matrix"]
            assert greater_term_matrix == equal_term_matrix != less_term_matrix

        # Check that raw matrices are created
        for term in ["lt", "gt", "eq"]:
            res = client.get(
                f"/v1/studies/{study_id}/raw",
                params={"path": f"input/bindingconstraints/{bc_id_w_matrix}_{term}", "depth": 1, "formatted": True},  # type: ignore
                headers=admin_headers,
            )
            assert res.status_code == 200, res.json()
            data = res.json()["data"]
            if term == "lt":
                assert data == matrix_lt3.tolist()
            else:
                assert data == np.zeros((matrix_lt3.shape[0], 1)).tolist()

        # =============================
        #  UPDATE
        # =============================

        # Add a group
        grp_name = "random_grp"
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_matrix}",
            json={"group": grp_name},
            headers=admin_headers,
        )
        assert res.status_code == 200, res.json()
        assert res.json()["group"] == grp_name

        # Update matrix_term
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_matrix}",
            json={"greater_term_matrix": matrix_lt3.tolist()},
            headers=admin_headers,
        )
        assert res.status_code == 200, res.json()

        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": f"input/bindingconstraints/{bc_id_w_matrix}_gt"},
            headers=admin_headers,
        )
        assert res.status_code == 200, res.json()
        assert res.json()["data"] == matrix_lt3.tolist()

        # The user changed the timeStep to daily instead of hourly.
        # We must check that the matrices have been updated.
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_matrix}",
            json={"timeStep": "daily"},
            headers=admin_headers,
        )
        assert res.status_code == 200, res.json()

        if study_type == "variant":
            # Check the last command is a change on `time_step` field only
            res = client.get(f"/v1/studies/{study_id}/commands", headers=admin_headers)
            commands = res.json()
            command_args = commands[-1]["args"]
            assert command_args["time_step"] == "daily"
            assert "values" not in command_args
            assert (
                command_args["less_term_matrix"]
                == command_args["greater_term_matrix"]
                == command_args["equal_term_matrix"]
                is not None
            )

        # Check that the matrices are daily/weekly matrices
        expected_matrix = np.zeros((366, 1))
        for term_alias in ["lt", "gt", "eq"]:
            res = client.get(
                f"/v1/studies/{study_id}/raw",
                params={
                    "path": f"input/bindingconstraints/{bc_id_w_matrix}_{term_alias}",
                    "depth": 1,
                    "formatted": True,
                },  # type: ignore
                headers=admin_headers,
            )
            assert res.status_code == 200, res.json()
            assert res.json()["data"] == expected_matrix.tolist()

        # =============================
        #  DELETE
        # =============================

        # Delete a binding constraint
        res = client.delete(f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_group}", headers=admin_headers)
        assert res.status_code == 200, res.json()

        # Asserts that the deletion worked
        res = client.get(f"/v1/studies/{study_id}/bindingconstraints", headers=admin_headers)
        assert len(res.json()) == 2

        # =============================
        #  ERRORS
        # =============================

        # Creation with wrong matrix according to version
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={
                "name": "binding_constraint_700",
                "enabled": True,
                "timeStep": "hourly",
                "operator": "less",
                "terms": [],
                "comments": "New API",
                "values": [[]],
            },
            headers=admin_headers,
        )
        assert res.status_code == 422, res.json()
        assert res.json()["description"] == "You cannot fill 'values' as it refers to the matrix before v8.7"

        # Update with old matrices
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_matrix}",
            json={"values": [[]]},
            headers=admin_headers,
        )
        assert res.status_code == 422, res.json()
        assert res.json()["exception"] == "InvalidFieldForVersionError"
        assert res.json()["description"] == "You cannot fill 'values' as it refers to the matrix before v8.7"

        # Creation with 2 matrices with different columns size
        bc_id_with_wrong_matrix = "binding_constraint_with_wrong_matrix"
        matrix_lt3 = np.ones((8784, 3))
        matrix_gt2 = np.ones((8784, 2))  # Wrong number of columns
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={
                "name": bc_id_with_wrong_matrix,
                "less_term_matrix": matrix_lt3.tolist(),
                "greater_term_matrix": matrix_gt2.tolist(),
                **args,
            },
            headers=admin_headers,
        )
        assert res.status_code == 422, res.json()
        exception = res.json()["exception"]
        description = res.json()["description"]
        assert exception == "RequestValidationError"
        assert "'less_term_matrix'" in description
        assert "'greater_term_matrix'" in description
        assert "(8784, 3)" in description
        assert "(8784, 2)" in description

        #
        # Creation of 1 BC
        # Update raw with wrong columns size -> OK but validation should fail
        #

        matrix_lt3 = np.ones((8784, 3))
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={
                "name": "First BC",
                "less_term_matrix": matrix_lt3.tolist(),
                "group": "Group 1",
                **args,
            },
            headers=admin_headers,
        )
        assert res.status_code in {200, 201}, res.json()
        first_bc_id = res.json()["id"]

        generator = np.random.default_rng(11)
        random_matrix = pd.DataFrame(generator.integers(0, 10, size=(4, 1)))
        _upload_matrix(
            client,
            admin_access_token,
            study_id,
            f"input/bindingconstraints/{first_bc_id}_gt",
            random_matrix,
        )

        # Validation should fail
        res = client.get(
            f"/v1/studies/{study_id}/constraint-groups/Group 1/validate",
            headers=admin_headers,
        )
        assert res.status_code == 422
        obj = res.json()
        assert obj["exception"] == "WrongMatrixHeightError"
        assert obj["description"] == "The binding constraint 'First BC' should have 8784 rows, currently: 4"

        # So, we correct the shape of the matrix
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{first_bc_id}",
            json={"greater_term_matrix": matrix_lt3.tolist()},
            headers=admin_headers,
        )
        assert res.status_code in {200, 201}, res.json()

        #
        # Creation of another BC inside the same group with different columns size
        # "Second BC": 4 cols, "Group 1" -> OK, but should fail in group validation
        #

        # Asserts everything is ok.
        res = client.get(
            f"/v1/studies/{study_id}/constraint-groups/Group 1/validate",
            headers=admin_headers,
        )
        assert res.status_code == 200, res.json()

        matrix_gt4 = np.ones((8784, 4))  # Wrong number of columns
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={
                "name": "Second BC",
                "greater_term_matrix": matrix_gt4.tolist(),
                "group": "group 1",  # Same group, but different case
                **args,
            },
            headers=admin_headers,
        )
        assert res.status_code in {200, 201}, res.json()
        second_bc_id = res.json()["id"]

        # validate the BC group "Group 1"
        res = client.get(f"/v1/studies/{study_id}/constraint-groups/Group 1/validate", headers=admin_headers)
        assert res.status_code == 422, res.json()
        assert res.json()["exception"] == "MatrixWidthMismatchError"
        description = res.json()["description"]
        assert re.search(r"the most common width in the group is 3", description, flags=re.IGNORECASE)
        assert re.search(r"'second bc_gt' has 4 columns", description, flags=re.IGNORECASE)

        # So, we correct the shape of the matrix of the Second BC
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{second_bc_id}",
            json={"greater_term_matrix": matrix_lt3.tolist()},
            headers=admin_headers,
        )
        assert res.status_code in {200, 201}, res.json()

        #
        # Updating the group of a bc creates different columns size inside the same group
        # first_bc: 3 cols, "Group 1" -> OK
        # third_bd: 4 cols, "Group 2" -> OK
        # third_bd group changes to group1 -> Fails validation
        #

        matrix_lt4 = np.ones((8784, 4))
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={
                "name": "Third BC",
                "less_term_matrix": matrix_lt4.tolist(),
                "group": "Group 2",
                **args,
            },
            headers=admin_headers,
        )
        assert res.status_code in {200, 201}, res.json()
        third_bd_id = res.json()["id"]

        res = client.put(
            f"v1/studies/{study_id}/bindingconstraints/{third_bd_id}",
            json={"group": "Group 1"},
            headers=admin_headers,
        )
        # This should succeed but cause the validation endpoint to fail.
        assert res.status_code in {200, 201}, res.json()

        # validate the BC group "Group 1"
        res = client.get(f"/v1/studies/{study_id}/constraint-groups/Group 1/validate", headers=admin_headers)
        assert res.status_code == 422, res.json()
        assert res.json()["exception"] == "MatrixWidthMismatchError"
        description = res.json()["description"]
        assert re.search(r"the most common width in the group is 3", description, flags=re.IGNORECASE)
        assert re.search(r"'third bc_lt' has 4 columns", description, flags=re.IGNORECASE)

        # So, we correct the shape of the matrix of the Second BC
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{third_bd_id}",
            json={"greater_term_matrix": matrix_lt3.tolist()},
            headers=admin_headers,
        )
        assert res.status_code in {200, 201}, res.json()

        #
        # Update causes different matrices size inside the same bc
        # second_bc: 1st matrix has 4 cols and others 1 -> OK
        # second_bc: 1st matrix has 4 cols and 2nd matrix has 3 cols -> Fails validation
        #

        res = client.put(
            f"v1/studies/{study_id}/bindingconstraints/{second_bc_id}",
            json={"group": "Group 2"},
            headers=admin_headers,
        )
        assert res.status_code in {200, 201}, res.json()

        # validate the "Group 2": for the moment the BC is valid
        res = client.get(f"/v1/studies/{study_id}/constraint-groups/Group 2/validate", headers=admin_headers)
        assert res.status_code in {200, 201}, res.json()

        res = client.put(
            f"v1/studies/{study_id}/bindingconstraints/{second_bc_id}",
            json={"greater_term_matrix": matrix_gt4.tolist()},
            headers=admin_headers,
        )
        # This should succeed but cause the validation endpoint to fail.
        assert res.status_code in {200, 201}, res.json()

        # Collect all the binding constraints groups
        res = client.get(f"/v1/studies/{study_id}/constraint-groups", headers=admin_headers)
        assert res.status_code in {200, 201}, res.json()
        groups = res.json()
        assert set(groups) == {"default", "random_grp", "Group 1", "Group 2"}
        assert groups["Group 2"] == [
            {
                "comments": "New API",
                "terms": [],
                "enabled": True,
                "filterSynthesis": "",
                "filterYearByYear": "",
                "group": "Group 2",
                "id": "second bc",
                "name": "Second BC",
                "operator": "less",
                "timeStep": "hourly",
            }
        ]

        # Validate all binding constraints groups
        res = client.get(f"/v1/studies/{study_id}/constraint-groups/validate-all", headers=admin_headers)
        assert res.status_code == 422, res.json()
        exception = res.json()["exception"]
        description = res.json()["description"]
        assert exception == "MatrixWidthMismatchError"
        assert re.search(r"'Group 1':", description, flags=re.IGNORECASE)
        assert re.search(r"the most common width in the group is 3", description, flags=re.IGNORECASE)
        assert re.search(r"'third bc_lt' has 4 columns", description, flags=re.IGNORECASE)
