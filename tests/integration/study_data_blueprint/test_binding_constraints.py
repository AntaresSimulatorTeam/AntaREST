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

    def test_lifecycle__nominal(self, client: TestClient, user_access_token: str) -> None:
        user_headers = {"Authorization": f"Bearer {user_access_token}"}

        # Create a Study
        res = client.post(
            "/v1/studies",
            headers=user_headers,
            params={"name": "foo"},
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

        # Create Binding Constraints
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={
                "name": "Binding Constraint 1",
                "enabled": True,
                "time_step": "hourly",
                "operator": "less",
                "coeffs": {},
                "comments": "",
            },
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()

        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={
                "name": "Binding Constraint 2",
                "enabled": True,
                "time_step": "hourly",
                "operator": "less",
                "coeffs": {},
                "comments": "",
            },
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()

        # Asserts that creating 2 binding constraints with the same name raises an Exception
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={
                "name": "Binding Constraint 1",
                "enabled": True,
                "time_step": "hourly",
                "operator": "less",
                "coeffs": {},
                "comments": "",
            },
            headers=user_headers,
        )
        assert res.status_code == 409, res.json()

        # Get Binding Constraint list to check created binding constraints
        res = client.get(f"/v1/studies/{study_id}/bindingconstraints", headers=user_headers)
        binding_constraints_list = res.json()
        expected = [
            {
                "id": "binding constraint 1",
                "name": "Binding Constraint 1",
                "enabled": True,
                "time_step": "hourly",
                "operator": "less",
                "constraints": None,  # terms
                "values": None,
                "filter_year_by_year": "",
                "filter_synthesis": "",
                "comments": "",
            },
            {
                "id": "binding constraint 2",
                "name": "Binding Constraint 2",
                "enabled": True,
                "time_step": "hourly",
                "operator": "less",
                "constraints": None,  # terms
                "values": None,
                "filter_year_by_year": "",
                "filter_synthesis": "",
                "comments": "",
            },
        ]
        assert binding_constraints_list == expected

        bc_id = binding_constraints_list[0]["id"]

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
                },  # NOTE: cluster_id in term data can be uppercase, but it must be lowercase in the returned ini configuration file
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

        # Create Variant
        res = client.post(
            f"/v1/studies/{study_id}/variants",
            headers=user_headers,
            params={"name": "Variant 1"},
        )
        assert res.status_code == 200, res.json()
        variant_id = res.json()

        # Create Binding constraints
        res = client.post(
            f"/v1/studies/{variant_id}/commands",
            json=[
                {
                    "action": "create_binding_constraint",
                    "args": {
                        "name": "binding_constraint_3",
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
        assert res.status_code == 200, res.json()

        res = client.post(
            f"/v1/studies/{variant_id}/commands",
            json=[
                {
                    "action": "create_binding_constraint",
                    "args": {
                        "name": "binding_constraint_4",
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
        assert res.status_code == 200, res.json()

        # Get Binding Constraint list
        res = client.get(f"/v1/studies/{variant_id}/bindingconstraints", headers=user_headers)
        binding_constraints_list = res.json()
        assert res.status_code == 200, res.json()
        assert len(binding_constraints_list) == 4
        assert binding_constraints_list[2]["id"] == "binding_constraint_3"
        assert binding_constraints_list[3]["id"] == "binding_constraint_4"

        bc_id = binding_constraints_list[2]["id"]

        # Update element of Binding constraint
        new_comment = "We made it !"
        res = client.put(
            f"v1/studies/{variant_id}/bindingconstraints/{bc_id}",
            json={"key": "comments", "value": new_comment},
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()

        # Get Binding Constraint
        res = client.get(
            f"/v1/studies/{variant_id}/bindingconstraints/{bc_id}",
            headers=user_headers,
        )
        binding_constraint = res.json()
        comments = binding_constraint["comments"]
        assert res.status_code == 200, res.json()
        assert comments == new_comment

        # Add Binding Constraint term

        res = client.post(
            f"/v1/studies/{variant_id}/bindingconstraints/{bc_id}/term",
            json={
                "weight": 1,
                "offset": 2,
                "data": {"area1": area1_id, "area2": area2_id},
            },
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()

        # Get Binding Constraint
        res = client.get(
            f"/v1/studies/{variant_id}/bindingconstraints/{bc_id}",
            headers=user_headers,
        )
        binding_constraint = res.json()
        constraints = binding_constraint["constraints"]
        assert res.status_code == 200, res.json()
        assert binding_constraint["id"] == bc_id
        assert len(constraints) == 1
        assert constraints[0]["id"] == f"{area1_id}%{area2_id}"
        assert constraints[0]["weight"] == 1
        assert constraints[0]["offset"] == 2
        assert constraints[0]["data"]["area1"] == area1_id
        assert constraints[0]["data"]["area2"] == area2_id

        # Update Constraint term
        res = client.put(
            f"/v1/studies/{variant_id}/bindingconstraints/{bc_id}/term",
            json={
                "id": f"{area1_id}%{area2_id}",
                "weight": 3,
            },
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()

        # Get Binding Constraint
        res = client.get(
            f"/v1/studies/{variant_id}/bindingconstraints/{bc_id}",
            headers=user_headers,
        )
        binding_constraint = res.json()
        constraints = binding_constraint["constraints"]
        assert res.status_code == 200, res.json()
        assert binding_constraint["id"] == bc_id
        assert len(constraints) == 1
        assert constraints[0]["id"] == f"{area1_id}%{area2_id}"
        assert constraints[0]["weight"] == 3
        assert constraints[0]["offset"] is None
        assert constraints[0]["data"]["area1"] == area1_id
        assert constraints[0]["data"]["area2"] == area2_id

        # Remove Constraint term
        res = client.delete(
            f"/v1/studies/{variant_id}/bindingconstraints/{bc_id}/term/{area1_id}%{area2_id}",
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()

        # Get Binding Constraint
        res = client.get(
            f"/v1/studies/{variant_id}/bindingconstraints/{bc_id}",
            headers=user_headers,
        )
        binding_constraint = res.json()
        constraints = binding_constraint["constraints"]
        assert res.status_code == 200, res.json()
        assert constraints is None

        # Creates a binding constraint with the new API
        res = client.post(
            f"/v1/studies/{variant_id}/bindingconstraints",
            json={
                "name": "binding_constraint_5",
                "enabled": True,
                "time_step": "hourly",
                "operator": "less",
                "coeffs": {},
                "comments": "New API",
            },
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()

        # Asserts that creating 2 binding constraints with the same name raises an Exception
        res = client.post(
            f"/v1/studies/{variant_id}/bindingconstraints",
            json={
                "name": "binding_constraint_5",
                "enabled": True,
                "time_step": "hourly",
                "operator": "less",
                "coeffs": {},
                "comments": "New API",
            },
            headers=user_headers,
        )
        assert res.status_code == 409, res.json()
        assert res.json() == {
            "description": "A binding constraint with the same name already exists: binding_constraint_5.",
            "exception": "DuplicateConstraintName",
        }

        # Assert empty name
        res = client.post(
            f"/v1/studies/{variant_id}/bindingconstraints",
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
            f"/v1/studies/{variant_id}/bindingconstraints",
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

        # Asserts that 5 binding constraints have been created
        res = client.get(f"/v1/studies/{variant_id}/bindingconstraints", headers=user_headers)
        assert res.status_code == 200, res.json()
        assert len(res.json()) == 5

        # The user change the time_step to daily instead of hourly.
        # We must check that the matrix is a daily/weekly matrix.
        res = client.put(
            f"/v1/studies/{variant_id}/bindingconstraints/{bc_id}",
            json={"key": "time_step", "value": "daily"},
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()

        # Check the last command is a change time_step
        res = client.get(f"/v1/studies/{variant_id}/commands", headers=user_headers)
        commands = res.json()
        args = commands[-1]["args"]
        assert args["time_step"] == "daily"
        assert args["values"] is not None, "We should have a matrix ID (sha256)"

        # Check that the matrix is a daily/weekly matrix
        res = client.get(
            f"/v1/studies/{variant_id}/raw",
            params={"path": f"input/bindingconstraints/{bc_id}", "depth": 1, "formatted": True},
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()
        dataframe = res.json()
        assert len(dataframe["index"]) == 366
        assert len(dataframe["columns"]) == 3  # less, equal, greater
