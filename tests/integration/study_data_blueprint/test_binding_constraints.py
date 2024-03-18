import numpy as np
import pytest
from starlette.testclient import TestClient

from antarest.study.business.binding_constraint_management import AreaClusterDTO, AreaLinkDTO, ConstraintTermDTO


class TestAreaLinkDTO:
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
        info = AreaLinkDTO(area1=area1, area2=area2)
        assert info.generate_id() == expected


class TestAreaClusterDTO:
    @pytest.mark.parametrize(
        "area, cluster, expected",
        [
            ("Area 1", "Cluster X", "area 1.cluster x"),
            ("de", "Nuclear", "de.nuclear"),
            ("GB", "Gas", "gb.gas"),
        ],
    )
    def test_constraint_id(self, area: str, cluster: str, expected: str) -> None:
        info = AreaClusterDTO(area=area, cluster=cluster)
        assert info.generate_id() == expected


class TestConstraintTermDTO:
    def test_constraint_id__link(self):
        term = ConstraintTermDTO(
            id="foo",
            weight=3.14,
            offset=123,
            data=AreaLinkDTO(area1="Area 1", area2="Area 2"),
        )
        assert term.generate_id() == term.data.generate_id()

    def test_constraint_id__cluster(self):
        term = ConstraintTermDTO(
            id="foo",
            weight=3.14,
            offset=123,
            data=AreaClusterDTO(area="Area 1", cluster="Cluster X"),
        )
        assert term.generate_id() == term.data.generate_id()

    def test_constraint_id__other(self):
        term = ConstraintTermDTO(
            id="foo",
            weight=3.14,
            offset=123,
        )
        assert term.generate_id() == "foo"


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
                "time_step": "hourly",
                "operator": "less",
                "coeffs": {},
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
                "constraints": None,
                "enabled": True,
                "filter_synthesis": "",
                "filter_year_by_year": "",
                "id": "binding_constraint_1",
                "name": "binding_constraint_1",
                "operator": "less",
                "time_step": "hourly",
            },
            {
                "comments": "",
                "constraints": None,
                "enabled": True,
                "filter_synthesis": "",
                "filter_year_by_year": "",
                "id": "binding_constraint_2",
                "name": "binding_constraint_2",
                "operator": "less",
                "time_step": "hourly",
            },
            {
                "comments": "New API",
                "constraints": None,
                "enabled": True,
                "filter_synthesis": "",
                "filter_year_by_year": "",
                "id": "binding_constraint_3",
                "name": "binding_constraint_3",
                "operator": "less",
                "time_step": "hourly",
            },
        ]
        assert binding_constraints_list == expected

        bc_id = binding_constraints_list[0]["id"]

        # Asserts binding constraint configuration is always valid.
        res = client.get(f"/v1/studies/{study_id}/bindingconstraints/{bc_id}/validate", headers=user_headers)
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
        constraint_terms = binding_constraint["constraints"]
        expected = [
            {
                "data": {"area1": area1_id, "area2": area2_id},
                "id": f"{area1_id}%{area2_id}",
                "offset": 2.0,
                "weight": 1.0,
            },
            {
                "data": {"area": area1_id, "cluster": cluster_id.lower()},
                "id": f"{area1_id}.{cluster_id.lower()}",
                "offset": 2.0,
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
        constraint_terms = binding_constraint["constraints"]
        expected = [
            {
                "data": {"area1": area1_id, "area2": area2_id},
                "id": f"{area1_id}%{area2_id}",
                "offset": 2.0,
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
        assert res.status_code == 200, res.json()

        # Get Binding Constraint
        res = client.get(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id}",
            headers=user_headers,
        )
        binding_constraint = res.json()
        comments = binding_constraint["comments"]
        assert res.status_code == 200, res.json()
        assert comments == new_comment

        # The user change the time_step to daily instead of hourly.
        # We must check that the matrix is a daily/weekly matrix.
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id}",
            json={"time_step": "daily"},
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()

        # Check the last command is a change time_step
        if study_type == "variant":
            res = client.get(f"/v1/studies/{study_id}/commands", headers=user_headers)
            commands = res.json()
            args = commands[-1]["args"]
            assert args["time_step"] == "daily"
            assert args["values"] is not None, "We should have a matrix ID (sha256)"

        # Check that the matrix is a daily/weekly matrix
        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": f"input/bindingconstraints/{bc_id}", "depth": 1, "formatted": True},
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
                "time_step": "hourly",
                "operator": "less",
                "coeffs": {},
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
                "time_step": "hourly",
                "operator": "less",
                "coeffs": {},
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
                "time_step": "hourly",
                "operator": "less",
                "coeffs": {},
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
                "time_step": "hourly",
                "operator": "less",
                "coeffs": {},
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
                "time_step": "hourly",
                "operator": "less",
                "coeffs": {},
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
            "time_step": "daily",
            "operator": "less",
            "coeffs": {},
            "comments": "Creation with matrix",
            "values": wrong_matrix.tolist(),
        }
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json=wrong_request_args,
            headers=user_headers,
        )
        assert res.status_code == 500
        exception = res.json()["exception"]
        description = res.json()["description"]
        assert exception == "ValueError" if study_type == "variant" else "CommandApplicationError"
        assert f"Invalid matrix shape {wrong_matrix.shape}, expected (366, 3)" in description

        # Delete a fake binding constraint
        res = client.delete(f"/v1/studies/{study_id}/bindingconstraints/fake_bc", headers=user_headers)
        assert res.status_code == 500
        assert res.json()["exception"] == "CommandApplicationError"
        assert res.json()["description"] == "Binding constraint not found"

        # Add a group before v8.7
        grp_name = "random_grp"
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/binding_constraint_2",
            json={"group": grp_name},
            headers=user_headers,
        )
        assert res.status_code == 422
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
        assert res.status_code == 422
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
        args = {"enabled": True, "time_step": "hourly", "operator": "less", "coeffs": {}, "comments": "New API"}
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={"name": bc_id_wo_group, **args},
            headers=admin_headers,
        )
        assert res.status_code in {200, 201}, res.json()

        res = client.get(f"/v1/studies/{study_id}/bindingconstraints/{bc_id_wo_group}", headers=admin_headers)
        assert res.json()["group"] == "default"

        # Creation of bc with a group
        bc_id_w_group = "binding_constraint_2"
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={"name": bc_id_w_group, "group": "specific_grp", **args},
            headers=admin_headers,
        )
        assert res.status_code in {200, 201}, res.json()

        res = client.get(f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_group}", headers=admin_headers)
        assert res.json()["group"] == "specific_grp"

        # Creation of bc with a matrix
        bc_id_w_matrix = "binding_constraint_3"
        matrix_lt = np.ones((8784, 3))
        matrix_lt_to_list = matrix_lt.tolist()
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={"name": bc_id_w_matrix, "less_term_matrix": matrix_lt_to_list, **args},
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
                params={"path": f"input/bindingconstraints/{bc_id_w_matrix}_{term}", "depth": 1, "formatted": True},
                headers=admin_headers,
            )
            assert res.status_code == 200
            data = res.json()["data"]
            if term == "lt":
                assert data == matrix_lt_to_list
            else:
                assert data == np.zeros((matrix_lt.shape[0], 1)).tolist()

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

        # Asserts the groupe is created
        res = client.get(f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_matrix}", headers=admin_headers)
        assert res.json()["group"] == grp_name

        # Update matrix_term
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_matrix}",
            json={"greater_term_matrix": matrix_lt_to_list},
            headers=admin_headers,
        )
        assert res.status_code == 200, res.json()

        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": f"input/bindingconstraints/{bc_id_w_matrix}_gt"},
            headers=admin_headers,
        )
        assert res.status_code == 200
        assert res.json()["data"] == matrix_lt_to_list

        # The user changed the time_step to daily instead of hourly.
        # We must check that the matrices have been updated.
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_matrix}",
            json={"time_step": "daily"},
            headers=admin_headers,
        )
        assert res.status_code == 200, res.json()

        if study_type == "variant":
            # Check the last command is a change time_step
            res = client.get(f"/v1/studies/{study_id}/commands", headers=admin_headers)
            commands = res.json()
            command_args = commands[-1]["args"]
            assert command_args["time_step"] == "daily"
            assert (
                command_args["less_term_matrix"]
                == command_args["greater_term_matrix"]
                == command_args["equal_term_matrix"]
                is not None
            )

        # Check that the matrices are daily/weekly matrices
        expected_matrix = np.zeros((366, 1)).tolist()
        for term_alias in ["lt", "gt", "eq"]:
            res = client.get(
                f"/v1/studies/{study_id}/raw",
                params={
                    "path": f"input/bindingconstraints/{bc_id_w_matrix}_{term_alias}",
                    "depth": 1,
                    "formatted": True,
                },
                headers=admin_headers,
            )
            assert res.status_code == 200
            assert res.json()["data"] == expected_matrix

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
                "time_step": "hourly",
                "operator": "less",
                "coeffs": {},
                "comments": "New API",
                "values": [[]],
            },
            headers=admin_headers,
        )
        assert res.status_code == 422
        assert res.json()["description"] == "You cannot fill 'values' as it refers to the matrix before v8.7"

        # Update with old matrices
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_matrix}",
            json={"values": [[]]},
            headers=admin_headers,
        )
        assert res.status_code == 422
        assert res.json()["exception"] == "InvalidFieldForVersionError"
        assert res.json()["description"] == "You cannot fill 'values' as it refers to the matrix before v8.7"

        # Creation with 2 matrices with different columns size
        bc_id_with_wrong_matrix = "binding_constraint_with_wrong_matrix"
        matrix_lt = np.ones((8784, 3))
        matrix_gt = np.ones((8784, 2))
        matrix_gt_to_list = matrix_gt.tolist()
        matrix_lt_to_list = matrix_lt.tolist()
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={
                "name": bc_id_with_wrong_matrix,
                "less_term_matrix": matrix_lt_to_list,
                "greater_term_matrix": matrix_gt_to_list,
                **args,
            },
            headers=admin_headers,
        )
        assert res.status_code == 422
        assert res.json()["exception"] == "IncoherenceBetweenMatricesLength"
        assert (
            res.json()["description"]
            == "The matrices of binding_constraint_with_wrong_matrix must have the same number of columns, currently {2, 3}"
        )

        # fixme: a changer

        #
        # Creation of 2 bc inside the same group with different columns size
        # first_bc: 3 cols, group1
        # second_bc: 4 cols, group1 -> Should fail
        #

        first_bc = "binding_constraint_validation"
        matrix_lt = np.ones((8784, 3))
        matrix_lt_to_list = matrix_lt.tolist()
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={"name": first_bc, "less_term_matrix": matrix_lt_to_list, "group": "group1", **args},
            headers=admin_headers,
        )
        assert res.status_code in {200, 201}, res.json()

        matrix_gt = np.ones((8784, 4))
        matrix_gt_to_list = matrix_gt.tolist()
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={"name": "other_bc", "greater_term_matrix": matrix_gt_to_list, "group": "group1", **args},
            headers=admin_headers,
        )
        assert res.status_code == 422
        assert res.json()["exception"] == "IncoherenceBetweenMatricesLength"
        assert res.json()["description"] == "The matrices of the group group1 do not have the same number of columns"

        #
        # Updating the group of a bc creates different columns size inside the same group
        # first_bc: 3 cols, group 1
        # second_bc: 4 cols, group2 -> OK
        # second_bc group changes to group1 -> Fails validation
        #

        second_bc = "binding_constraint_validation_2"
        matrix_lt = np.ones((8784, 4))
        matrix_lt_to_list = matrix_lt.tolist()
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={"name": second_bc, "less_term_matrix": matrix_lt_to_list, "group": "group2", **args},
            headers=admin_headers,
        )
        assert res.status_code in {200, 201}, res.json()

        res = client.put(
            f"v1/studies/{study_id}/bindingconstraints/{second_bc}",
            json={"group": "group1"},
            headers=admin_headers,
        )
        # This should succeed but cause the validation endpoint to fail.
        assert res.status_code in {200, 201}, res.json()

        res = client.get(f"/v1/studies/{study_id}/bindingconstraints/{second_bc}/validate", headers=admin_headers)
        assert res.status_code == 422
        assert res.json()["exception"] == "IncoherenceBetweenMatricesLength"
        assert res.json()["description"] == "The matrices of the group group1 do not have the same number of columns"

        #
        # Update causes different matrices size inside the same bc
        # second_bc: 1st matrix has 4 cols and others 1 -> OK
        # second_bc: 1st matrix has 4 cols and 2nd matrix has 3 cols -> Fails validation
        #

        res = client.put(
            f"v1/studies/{study_id}/bindingconstraints/{second_bc}", json={"group": "group2"}, headers=admin_headers
        )
        assert res.status_code in {200, 201}, res.json()
        # For the moment the bc is valid
        res = client.get(f"/v1/studies/{study_id}/bindingconstraints/{second_bc}/validate", headers=admin_headers)
        assert res.status_code in {200, 201}, res.json()

        matrix_lt_3 = np.ones((8784, 3))
        matrix_lt_3_to_list = matrix_lt_3.tolist()
        res = client.put(
            f"v1/studies/{study_id}/bindingconstraints/{second_bc}",
            json={"greater_term_matrix": matrix_lt_3_to_list},
            headers=admin_headers,
        )
        # This should succeed but cause the validation endpoint to fail.
        assert res.status_code in {200, 201}, res.json()

        res = client.get(f"/v1/studies/{study_id}/bindingconstraints/{second_bc}/validate", headers=admin_headers)
        assert res.status_code == 422
        assert res.json()["exception"] == "IncoherenceBetweenMatricesLength"
        assert (
            res.json()["description"]
            == "The matrices of binding_constraint_validation_2 must have the same number of columns, currently {3, 4}"
        )

        #
        # Updating a matrix causes different matrices size inside the same group
        # first_bc: 3 cols, group1
        # second_bc: 3 cols, group1 -> OK
        # second_bc: update 2 matrices with 4 cols, group1 -> Fails validation
        #

        res = client.put(
            f"v1/studies/{study_id}/bindingconstraints/{second_bc}",
            json={"less_term_matrix": matrix_lt_3_to_list},
            headers=admin_headers,
        )
        assert res.status_code in {200, 201}, res.json()

        # For the moment the bc is valid
        res = client.get(f"/v1/studies/{study_id}/bindingconstraints/{second_bc}/validate", headers=admin_headers)
        assert res.status_code in {200, 201}, res.json()

        res = client.put(
            f"v1/studies/{study_id}/bindingconstraints/{second_bc}",
            json={"group": "group1"},
            headers=admin_headers,
        )
        assert res.status_code in {200, 201}, res.json()
        res = client.put(
            f"v1/studies/{study_id}/bindingconstraints/{second_bc}",
            json={"less_term_matrix": matrix_lt_to_list, "greater_term_matrix": matrix_lt_to_list},
            headers=admin_headers,
        )
        # This should succeed but cause the validation endpoint to fail.
        assert res.status_code in {200, 201}, res.json()

        res = client.get(f"/v1/studies/{study_id}/bindingconstraints/{second_bc}/validate", headers=admin_headers)
        assert res.status_code == 422
        assert res.json()["exception"] == "IncoherenceBetweenMatricesLength"
        assert res.json()["description"] == "The matrices of the group group1 do not have the same number of columns"
