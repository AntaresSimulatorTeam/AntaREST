# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import re
import time

import numpy as np
import pandas as pd
import pytest
from httpx._exceptions import HTTPError
from starlette.testclient import TestClient

from antarest.study.business.binding_constraint_management import ClusterTerm, ConstraintTerm, LinkTerm
from tests.integration.prepare_proxy import PreparerProxy

MATRIX_SIZES = {"hourly": 8784, "daily": 366, "weekly": 366}

REQUIRED_MATRICES = {
    "less": {"lt"},
    "equal": {"eq"},
    "greater": {"gt"},
    "both": {"lt", "gt"},
}


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
        assert term.data is not None
        assert term.generate_id() == term.data.generate_id()

    def test_constraint_id__cluster(self) -> None:
        term = ConstraintTerm(
            id="foo",
            weight=3.14,
            offset=123,
            data=ClusterTerm(area="Area 1", cluster="Cluster X"),
        )
        assert term.data is not None
        assert term.generate_id() == term.data.generate_id()

    def test_constraint_id__other(self) -> None:
        term = ConstraintTerm(
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

    def test_update_multiple_binding_constraints(self, client: TestClient, user_access_token: str) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=880)
        body = {}
        # Creates 50 BCs
        for k in range(50):
            bc_id = f"bc_{k}"
            client.post(
                f"/v1/studies/{study_id}/commands",
                json=[{"action": "create_binding_constraint", "args": {"name": bc_id}}],
            )
            body[bc_id] = {"filterSynthesis": "hourly"}
        # Modify all of them with the table-mode endpoints
        start = time.time()
        res = client.put(f"/v1/studies/{study_id}/table-mode/binding-constraints", json=body)
        assert res.status_code in {200, 201}
        end = time.time()
        duration = end - start
        # due to new code this should be extremely fast.
        assert duration < 0.2
        # asserts the changes are effective.
        res = client.get(f"/v1/studies/{study_id}/bindingconstraints")
        assert res.status_code == 200
        for bc in res.json():
            assert bc["filterSynthesis"] == "hourly"
        # create a variant from the study
        study_id = preparer.create_variant(study_id, name="var_1")
        # Update 10 BCs
        body = {}
        for k in range(10):
            body[f"bc_{k}"] = {"enabled": False}
        res = client.put(f"/v1/studies/{study_id}/table-mode/binding-constraints", json=body)
        assert res.status_code in {200, 201}
        # asserts changes are effective
        res = client.get(f"/v1/studies/{study_id}/bindingconstraints")
        assert res.status_code == 200
        for bc in res.json():
            bc_id = bc["id"]
            if int(bc_id[3:]) < 10:
                assert not bc["enabled"]
            else:
                assert bc["enabled"]
        # asserts commands used are update_binding_constraint
        res = client.get(f"/v1/studies/{study_id}/commands")
        assert res.status_code == 200
        json_result = res.json()
        assert len(json_result) == 1
        for cmd in json_result:
            assert cmd["action"] == "update_binding_constraints"
        # create another variant from the parent study
        study_id = preparer.create_variant(study_id, name="var_1")
        # update 50 BCs
        body = {}
        for k in range(49):
            body[f"bc_{k}"] = {"comments": "New comment !"}
        body["bc_49"] = {"time_step": "daily"}
        res = client.put(f"/v1/studies/{study_id}/table-mode/binding-constraints", json=body)
        assert res.status_code in {200, 201}
        # asserts changes are effective
        res = client.get(f"/v1/studies/{study_id}/bindingconstraints")
        assert res.status_code == 200
        for bc in res.json():
            bc_id = bc["id"]
            if int(bc_id[3:]) < 49:
                assert bc["comments"] == "New comment !"
            else:
                assert bc["timeStep"] == "daily"
        # asserts commands used are update_config and replace_matrix
        res = client.get(f"/v1/studies/{study_id}/commands")
        assert res.status_code == 200
        json_result = res.json()
        assert len(json_result) == 1
        assert json_result[0]["action"] == "update_binding_constraints"

    @pytest.mark.parametrize("study_type", ["raw", "variant"])
    def test_lifecycle__nominal(self, client: TestClient, user_access_token: str, study_type: str) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # =============================
        #  STUDY PREPARATION
        # =============================

        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=860)
        area1_id = preparer.create_area(study_id, name="Area 1")["id"]
        area2_id = preparer.create_area(study_id, name="Area 2")["id"]
        link_id = preparer.create_link(study_id, area1_id=area1_id, area2_id=area2_id)["id"]

        # Create a cluster in area1
        cluster_id = preparer.create_thermal(study_id, area1_id, name="Cluster 1", group="Nuclear")["id"]
        clusters_list = preparer.get_thermals(study_id, area1_id)
        assert len(clusters_list) == 1
        assert clusters_list[0]["id"] == cluster_id
        assert clusters_list[0]["name"] == "Cluster 1"
        assert clusters_list[0]["group"] == "nuclear"

        if study_type == "variant":
            study_id = preparer.create_variant(study_id, name="Variant 1")

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
        )
        assert res.status_code in {200, 201}, res.json()

        # Creates a binding constraint with the new API
        preparer.create_binding_constraint(
            study_id,
            name="binding_constraint_3",
            enabled=True,
            timeStep="hourly",
            operator="less",
            terms=[],
            comments="New API",
        )

        # Get Binding Constraint list
        binding_constraints_list = preparer.get_binding_constraints(study_id)
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
        res = client.get(f"/v1/studies/{study_id}/constraint-groups")
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
        )
        assert res.status_code == 200, res.json()

        # Add binding constraint cluster term
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id}/term",
            json={
                "weight": 1,
                "offset": 2,
                "data": {"area": area1_id, "cluster": cluster_id},
                # NOTE: cluster_id in term data can be uppercase, but it must be lowercase in the INI file
            },
        )
        assert res.status_code == 200, res.json()

        # Get binding constraints list to check added terms
        res = client.get(f"/v1/studies/{study_id}/bindingconstraints/{bc_id}")
        assert res.status_code == 200, res.json()
        binding_constraint = res.json()
        constraint_terms = binding_constraint["terms"]
        expected = [
            {
                "data": {"area1": area1_id, "area2": area2_id},
                "id": link_id,
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
            json={"id": f"{area1_id}.{cluster_id}", "weight": 3},
        )
        assert res.status_code == 200, res.json()

        # Check updated terms, cluster_id should be lowercase in the returned configuration
        res = client.get(f"/v1/studies/{study_id}/bindingconstraints/{bc_id}")
        assert res.status_code == 200, res.json()
        binding_constraint = res.json()
        constraint_terms = binding_constraint["terms"]
        expected = [
            {
                "data": {"area1": area1_id, "area2": area2_id},
                "id": link_id,
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
            json={"id": f"{area1_id}.!!invalid#cluster%%", "weight": 4},
        )
        assert res.status_code == 404, res.json()
        exception = res.json()["exception"]
        description = res.json()["description"]
        assert exception == "ConstraintTermNotFound"
        assert bc_id in description
        assert f"{area1_id}.!!invalid#cluster%%" in description

        # Update constraint cluster term with empty data
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id}/term",
            json={"id": f"{area1_id}.{cluster_id}", "data": {}},
        )
        assert res.status_code == 422, res.json()
        assert res.json() == {
            "body": {"data": {}, "id": f"{area1_id}.{cluster_id}"},
            "description": "Field required",
            "exception": "RequestValidationError",
        }

        # Remove Constraint term
        res = client.delete(f"/v1/studies/{study_id}/bindingconstraints/{bc_id}/term/{link_id}")
        assert res.status_code == 200, res.json()

        # Check updated terms, the deleted term should no longer exist.
        res = client.get(f"/v1/studies/{study_id}/bindingconstraints/{bc_id}")
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

        # Update random field, shouldn't remove the term.
        res = client.put(f"v1/studies/{study_id}/bindingconstraints/{bc_id}", json={"enabled": False})
        assert res.status_code == 200, res.json()

        res = client.get(f"/v1/studies/{study_id}/bindingconstraints/{bc_id}")
        assert res.status_code == 200, res.json()
        binding_constraint = res.json()
        constraint_terms = binding_constraint["terms"]
        assert constraint_terms == expected

        # =============================
        # GENERAL EDITION
        # =============================

        # Update element of Binding constraint
        new_comment = "We made it !"
        res = client.put(f"v1/studies/{study_id}/bindingconstraints/{bc_id}", json={"comments": new_comment})
        assert res.status_code == 200
        assert res.json()["comments"] == new_comment

        # The user change the timeStep to daily instead of hourly.
        # We must check that the matrix is a daily/weekly matrix.
        res = client.put(f"/v1/studies/{study_id}/bindingconstraints/{bc_id}", json={"timeStep": "daily"})
        assert res.status_code == 200, res.json()
        assert res.json()["timeStep"] == "daily"

        # Check that the command corresponds to a change in `time_step`
        if study_type == "variant":
            res = client.get(f"/v1/studies/{study_id}/commands")
            commands = res.json()
            args = commands[-1]["args"]
            assert args["time_step"] == "daily"
            assert args["values"] is not None, "We should have a matrix ID (sha256)"

        # Check that the matrix is a daily/weekly matrix
        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": f"input/bindingconstraints/{bc_id}", "depth": 1, "formatted": True},  # type: ignore
        )
        assert res.status_code == 200, res.json()
        dataframe = res.json()
        assert len(dataframe["index"]) == 366
        assert len(dataframe["columns"]) == 3  # less, equal, greater

        # =============================
        # CONSTRAINT DUPLICATION
        # =============================

        # Change source constraint matrix to ensure it will be copied correctly
        new_matrix = np.ones((366, 3)).tolist()
        res = client.post(
            f"/v1/studies/{study_id}/raw", params={"path": f"input/bindingconstraints/{bc_id}"}, json=new_matrix
        )
        res.raise_for_status()

        # Get the source constraint properties to ensure there are copied correctly
        res = client.get(f"/v1/studies/{study_id}/bindingconstraints/{bc_id}")
        res.raise_for_status()
        current_constraint = res.json()
        current_constraint.pop("name")
        current_constraint.pop("id")

        # Duplicates the constraint
        duplicated_name = "BC_4"
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id}", params={"new_constraint_name": duplicated_name}
        )
        res.raise_for_status()
        duplicated_constraint = res.json()

        # Asserts the duplicated constraint has the right name and the right properties
        assert duplicated_constraint.pop("name") == duplicated_name
        new_id = duplicated_constraint.pop("id")
        assert current_constraint == duplicated_constraint

        # Asserts the matrix is duplicated correctly
        res = client.get(f"/v1/studies/{study_id}/raw", params={"path": f"input/bindingconstraints/{new_id}"})
        res.raise_for_status()
        assert res.json()["data"] == new_matrix

        # =============================
        # ERRORS
        # =============================

        # Asserts duplication fails if given an non-exisiting constraint
        fake_name = "fake_name"
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints/{fake_name}", params={"new_constraint_name": "aa"}
        )
        assert res.status_code == 404
        assert res.json()["exception"] == "BindingConstraintNotFound"
        assert res.json()["description"] == f"Binding constraint '{fake_name}' not found"

        # Asserts duplication fails if given an already existing name
        res = client.post(f"/v1/studies/{study_id}/bindingconstraints/{bc_id}", params={"new_constraint_name": bc_id})
        assert res.status_code == 409
        assert res.json()["exception"] == "DuplicateConstraintName"
        assert res.json()["description"] == f"A binding constraint with the same name already exists: {bc_id}."

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
        )
        assert res.status_code == 422, res.json()
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
                "lessTermMatrix": [[]],
            },
        )
        assert res.status_code == 422, res.json()
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
        res = client.post(f"/v1/studies/{study_id}/bindingconstraints", json=wrong_request_args)
        assert res.status_code == 422, res.json()
        exception = res.json()["exception"]
        description = res.json()["description"]
        assert exception == "RequestValidationError"
        assert "'values'" in description
        assert "(366, 3)" in description

        # Delete a fake binding constraint
        res = client.delete(f"/v1/studies/{study_id}/bindingconstraints/fake_bc")
        assert res.status_code == 404, res.json()
        assert res.json()["exception"] == "BindingConstraintNotFound"
        assert res.json()["description"] == "Binding constraint 'fake_bc' not found"

        # Add a group before v8.7
        grp_name = "random_grp"
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/binding_constraint_2",
            json={"group": grp_name},
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
        )
        assert res.status_code == 422, res.json()
        assert res.json()["exception"] == "InvalidFieldForVersionError"
        assert res.json()["description"] == "You cannot fill a 'matrix_term' as these values refer to v8.7+ studies"

    @pytest.mark.parametrize("study_type", ["raw", "variant"])
    def test_for_version_870(self, client: TestClient, user_access_token: str, study_type: str) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}  # type: ignore

        # =============================
        #  STUDY PREPARATION
        # =============================

        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=870)

        if study_type == "variant":
            study_id = preparer.create_variant(study_id, name="Variant 1")

        # Create Areas, link and cluster
        area1_id = preparer.create_area(study_id, name="Area 1")["id"]
        area2_id = preparer.create_area(study_id, name="Area 2")["id"]
        link_id = preparer.create_link(study_id, area1_id=area1_id, area2_id=area2_id)["id"]
        cluster_id = preparer.create_thermal(study_id, area1_id, name="Cluster 1", group="Nuclear")["id"]

        # =============================
        #  CREATION
        # =============================

        # Creation of a bc without group
        bc_id_wo_group = "binding_constraint_1"
        args = {"enabled": True, "timeStep": "hourly", "operator": "less", "terms": [], "comments": "New API"}
        operator_1 = "lt"
        properties = preparer.create_binding_constraint(study_id, name=bc_id_wo_group, **args)
        assert properties["group"] == "default"

        # Creation of bc with a group
        bc_id_w_group = "binding_constraint_2"
        args["operator"], operator_2 = "greater", "gt"
        properties = preparer.create_binding_constraint(study_id, name=bc_id_w_group, group="specific_grp", **args)
        assert properties["group"] == "specific_grp"

        # Creation of bc with a matrix
        bc_id_w_matrix = "binding_constraint_3"
        matrix_lt3 = np.ones((8784, 3))
        args["operator"], operator_3 = "equal", "eq"
        # verify that trying to create a binding constraint with a less_term_matrix will
        # while using an `equal` operator will raise an error 422
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={"name": bc_id_w_matrix, "less_term_matrix": matrix_lt3.tolist(), **args},
        )
        assert res.status_code == 422, res.json()

        # now we create the binding constraint with the correct matrix
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={"name": bc_id_w_matrix, "equal_term_matrix": matrix_lt3.tolist(), **args},
        )
        res.raise_for_status()

        if study_type == "variant":
            res = client.get(f"/v1/studies/{study_id}/commands")
            last_cmd_args = res.json()[-1]["args"]
            less_term_matrix = last_cmd_args["less_term_matrix"]
            equal_term_matrix = last_cmd_args["equal_term_matrix"]
            greater_term_matrix = last_cmd_args["greater_term_matrix"]
            assert greater_term_matrix == less_term_matrix != equal_term_matrix

        # Check that raw matrices are created
        for bc_id, operator in zip(
            [bc_id_wo_group, bc_id_w_matrix, bc_id_w_group], [operator_1, operator_2, operator_3]
        ):
            for term in zip(
                [
                    bc_id_wo_group,
                    bc_id_w_matrix,
                ],
                ["lt", "gt", "eq"],
            ):
                path = f"input/bindingconstraints/{bc_id}_{term}"
                res = client.get(
                    f"/v1/studies/{study_id}/raw",
                    params={"path": path, "depth": 1, "formatted": True},  # type: ignore
                )
                # as we save only the operator matrix, we should have a matrix only for the operator
                if term != operator:
                    assert res.status_code == 404, res.json()
                    continue
                assert res.status_code == 200, res.json()
                data = res.json()["data"]
                if term == "lt":
                    assert data == matrix_lt3.tolist()
                else:
                    assert data == np.zeros((matrix_lt3.shape[0], 1)).tolist()

        # Checks that we only see existing matrices inside the Debug View
        res = client.get(f"/v1/studies/{study_id}/raw", params={"path": "/input/bindingconstraints", "depth": 1})
        assert res.status_code in {200, 201}
        assert res.json() == {
            f"{bc_id_wo_group}_lt": {},
            f"{bc_id_w_group}_gt": {},
            f"{bc_id_w_matrix}_eq": {},
            "bindingconstraints": {},
        }

        # =============================
        # CONSTRAINT TERM MANAGEMENT
        # =============================

        # Add binding constraint terms
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_group}/terms",
            json=[
                {"weight": 1, "offset": 2, "data": {"area1": area1_id, "area2": area2_id}},
                {"weight": 1, "offset": 2, "data": {"area": area1_id, "cluster": cluster_id}},
            ],
        )
        assert res.status_code == 200, res.json()

        # Attempt to add a term with missing data
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_group}/terms",
            json=[{"weight": 1, "offset": 2}],
        )
        assert res.status_code == 422, res.json()
        exception = res.json()["exception"]
        description = res.json()["description"]
        assert exception == "InvalidConstraintTerm"
        assert bc_id_w_group in description, "Error message should contain the binding constraint ID"
        assert "term 'data' is missing" in description, "Error message should indicate the missing field"

        # Attempt to add a duplicate term
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_group}/terms",
            json=[{"weight": 99, "offset": 0, "data": {"area1": area1_id, "area2": area2_id}}],
        )
        assert res.status_code == 409, res.json()
        exception = res.json()["exception"]
        description = res.json()["description"]
        assert exception == "DuplicateConstraintTerm"
        assert bc_id_w_group in description, "Error message should contain the binding constraint ID"
        assert link_id in description, "Error message should contain the duplicate term ID"

        # Get binding constraints list to check added terms
        res = client.get(f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_group}")
        assert res.status_code == 200, res.json()
        binding_constraint = res.json()
        constraint_terms = binding_constraint["terms"]
        expected = [
            {
                "data": {"area1": area1_id, "area2": area2_id},
                "id": link_id,
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

        # Update binding constraint terms
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_group}/terms",
            json=[
                {
                    "id": link_id,
                    "weight": 4.4,
                    "offset": 1,
                },
                {
                    "id": f"{area1_id}.{cluster_id}",
                    "weight": 5.1,
                    "data": {"area": area1_id, "cluster": cluster_id},
                },
            ],
        )
        assert res.status_code == 200, res.json()

        # Asserts terms were updated
        res = client.get(f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_group}")
        assert res.status_code == 200, res.json()
        binding_constraint = res.json()
        constraint_terms = binding_constraint["terms"]
        expected = [
            {
                "data": {"area1": area1_id, "area2": area2_id},
                "id": link_id,
                "offset": 1,
                "weight": 4.4,
            },
            {
                "data": {"area": area1_id, "cluster": cluster_id.lower()},
                "id": f"{area1_id}.{cluster_id.lower()}",
                "offset": None,
                "weight": 5.1,
            },
        ]
        assert constraint_terms == expected

        # =============================
        #  UPDATE
        # =============================

        # Add a group
        grp_name = "random_grp"
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_matrix}",
            json={"group": grp_name},
        )
        assert res.status_code == 200, res.json()
        assert res.json()["group"] == grp_name

        # check that updating of a binding constraint that has an operator "equal"
        # with a greater matrix will raise an error 422
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_matrix}",
            json={"greater_term_matrix": matrix_lt3.tolist()},
        )
        assert res.status_code == 422, res.json()
        assert "greater_term_matrix" in res.json()["description"]
        assert "equal" in res.json()["description"]
        assert res.json()["exception"] == "InvalidFieldForVersionError"

        # update the binding constraint operator first
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_matrix}",
            json={"operator": "greater"},
        )
        assert res.status_code == 200, res.json()

        # update the binding constraint matrix
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_matrix}",
            json={"greater_term_matrix": matrix_lt3.tolist()},
        )
        assert res.status_code == 200, res.json()

        # check that the matrix has been updated
        res = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": f"input/bindingconstraints/{bc_id_w_matrix}_gt"},
        )
        assert res.status_code == 200, res.json()
        assert res.json()["data"] == matrix_lt3.tolist()

        # The user changed the timeStep to daily instead of hourly.
        # We must check that the matrices have been updated.
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_matrix}",
            json={"timeStep": "daily"},
        )
        assert res.status_code == 200, res.json()

        if study_type == "variant":
            # Check the last command is a change on `time_step` field only
            res = client.get(f"/v1/studies/{study_id}/commands")
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
        for operator in ["less", "equal", "greater", "both"]:
            if operator != "both":
                res = client.put(
                    f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_matrix}",
                    json={"operator": operator, f"{operator}_term_matrix": expected_matrix.tolist()},
                )
            else:
                res = client.put(
                    f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_matrix}",
                    json={
                        "operator": operator,
                        "greater_term_matrix": expected_matrix.tolist(),
                        "less_term_matrix": expected_matrix.tolist(),
                    },
                )
            assert res.status_code == 200, res.json()
            for term_operator, term_alias in zip(["less", "equal", "greater"], ["lt", "eq", "gt"]):
                res = client.get(
                    f"/v1/studies/{study_id}/raw",
                    params={
                        "path": f"input/bindingconstraints/{bc_id_w_matrix}_{term_alias}",
                        "depth": 1,
                        "formatted": True,
                    },  # type: ignore
                )
                # check that update is made if no conflict between the operator and the matrix term alias
                if term_operator == operator or (operator == "both" and term_operator in ["less", "greater"]):
                    assert res.status_code == 200, res.json()
                    assert res.json()["data"] == expected_matrix.tolist()
                else:
                    assert res.status_code == 404, res.json()

        # set binding constraint operator to "less"
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_matrix}",
            json={"operator": "less"},
        )
        assert res.status_code == 200, res.json()

        # =============================
        #  DELETE
        # =============================

        # Delete a binding constraint
        res = client.delete(f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_group}")
        assert res.status_code == 200, res.json()

        # Asserts that the deletion worked
        binding_constraints_list = preparer.get_binding_constraints(study_id)
        assert len(binding_constraints_list) == 2

        # Delete multiple binding constraint
        preparer.create_binding_constraint(study_id, name="bc1", group="grp1", **args)
        preparer.create_binding_constraint(study_id, name="bc2", group="grp2", **args)

        binding_constraints_list = preparer.get_binding_constraints(study_id)
        assert len(binding_constraints_list) == 4

        res = client.request(
            "DELETE",
            f"/v1/studies/{study_id}/bindingconstraints",
            json=["bc1", "bc2"],
        )
        assert res.status_code == 200, res.json()

        # Asserts that the deletion worked
        binding_constraints_list = client.get(
            f"/v1/studies/{study_id}/raw",
            params={"path": "input/bindingconstraints/bindingconstraints"},  # type: ignore
        ).json()
        assert len(binding_constraints_list) == 2
        actual_ids = [constraint["id"] for constraint in binding_constraints_list.values()]
        assert actual_ids == ["binding_constraint_1", "binding_constraint_3"]
        keys = sorted(int(k) for k in binding_constraints_list.keys())
        assert keys == list(range(len(keys)))

        # =============================
        # CONSTRAINT DUPLICATION
        # =============================

        # Change source constraint matrix to ensure it will be copied correctly
        new_matrix = np.ones((366, 1)).tolist()
        res = client.post(
            f"/v1/studies/{study_id}/raw",
            params={"path": f"input/bindingconstraints/{bc_id_w_matrix}_lt"},
            json=new_matrix,
        )
        res.raise_for_status()

        # Get the source constraint properties to ensure there are copied correctly
        res = client.get(f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_matrix}")
        res.raise_for_status()
        current_constraint = res.json()
        current_constraint.pop("name")
        current_constraint.pop("id")

        # Duplicates the constraint
        duplicated_name = "BC_4"
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_matrix}",
            params={"new_constraint_name": duplicated_name},
        )
        res.raise_for_status()
        duplicated_constraint = res.json()

        # Asserts the duplicated constraint has the right name and the right properties
        assert duplicated_constraint.pop("name") == duplicated_name
        new_id = duplicated_constraint.pop("id")
        assert current_constraint == duplicated_constraint

        # Asserts the matrix is duplicated correctly
        res = client.get(f"/v1/studies/{study_id}/raw", params={"path": f"input/bindingconstraints/{new_id}_lt"})
        res.raise_for_status()
        assert res.json()["data"] == new_matrix

        # =============================
        #  ERRORS
        # =============================

        # Deletion multiple binding constraints, one does not exist. Make sure none is deleted

        binding_constraints_list = preparer.get_binding_constraints(study_id)
        assert len(binding_constraints_list) == 3

        res = client.request(
            "DELETE",
            f"/v1/studies/{study_id}/bindingconstraints",
            json=["binding_constraint_1", "binding_constraint_2", "binding_constraint_3"],
        )
        assert res.status_code == 404, res.json()
        assert res.json()["description"] == "Binding constraint(s) '['binding_constraint_2']' not found"

        binding_constraints_list = preparer.get_binding_constraints(study_id)
        assert len(binding_constraints_list) == 3

        # Creation with wrong matrix according to version
        for operator in ["less", "equal", "greater", "both"]:
            args["operator"] = operator
            res = client.post(
                f"/v1/studies/{study_id}/bindingconstraints",
                json={
                    "name": "binding_constraint_4",
                    "enabled": True,
                    "timeStep": "hourly",
                    "operator": operator,
                    "terms": [],
                    "comments": "New API",
                    "values": [[]],
                },
            )
            assert res.status_code == 422
            assert res.json()["description"] == "You cannot fill 'values' as it refers to the matrix before v8.7"

        # Update with old matrices
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{bc_id_w_matrix}",
            json={"values": [[]]},
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

        # update the args operator field to "greater"
        args["operator"] = "greater"

        matrix_gt3 = np.ones((8784, 3))
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={
                "name": "First BC",
                "greater_term_matrix": matrix_gt3.tolist(),
                "group": "Group 1",
                **args,
            },
        )
        assert res.status_code in {200, 201}, res.json()
        first_bc_id = res.json()["id"]

        generator = np.random.default_rng(11)
        random_matrix = pd.DataFrame(generator.integers(0, 10, size=(4, 1)))
        preparer.upload_matrix(study_id, f"input/bindingconstraints/{first_bc_id}_gt", random_matrix)

        # Validation should fail
        res = client.get(f"/v1/studies/{study_id}/constraint-groups/Group 1/validate")
        assert res.status_code == 422
        obj = res.json()
        assert obj["exception"] == "WrongMatrixHeightError"
        assert obj["description"] == "The binding constraint 'First BC' should have 8784 rows, currently: 4"

        # So, we correct the shape of the matrix
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{first_bc_id}",
            json={"greater_term_matrix": matrix_gt3.tolist()},
        )
        assert res.status_code in {200, 201}, res.json()

        #
        # Creation of another BC inside the same group with different columns size
        # "Second BC": 4 cols, "Group 1" -> OK, but should fail in group validation
        #

        # Asserts everything is ok.
        res = client.get(f"/v1/studies/{study_id}/constraint-groups/Group 1/validate")
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
        )
        assert res.status_code in {200, 201}, res.json()
        second_bc_id = res.json()["id"]

        # validate the BC group "Group 1"
        res = client.get(f"/v1/studies/{study_id}/constraint-groups/Group 1/validate")
        assert res.status_code == 422, res.json()
        assert res.json()["exception"] == "MatrixWidthMismatchError"
        description = res.json()["description"]
        assert re.search(r"the most common width in the group is 3", description, flags=re.IGNORECASE)
        assert re.search(r"'second bc_gt' has 4 columns", description, flags=re.IGNORECASE)

        # So, we correct the shape of the matrix of the Second BC
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{second_bc_id}",
            json={"greater_term_matrix": matrix_lt3.tolist()},
        )
        assert res.status_code in {200, 201}, res.json()

        #
        # Updating the group of a bc creates different columns size inside the same group
        # first_bc: 3 cols, "Group 1" -> OK
        # third_bd: 4 cols, "Group 2" -> OK
        # third_bd group changes to group1 -> Fails validation
        #

        args["operator"] = "less"
        matrix_lt4 = np.ones((8784, 4))
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={
                "name": "Third BC",
                "less_term_matrix": matrix_lt4.tolist(),
                "group": "Group 2",
                **args,
            },
        )
        assert res.status_code in {200, 201}, res.json()
        third_bd_id = res.json()["id"]

        res = client.put(
            f"v1/studies/{study_id}/bindingconstraints/{third_bd_id}",
            json={"group": "Group 1"},
        )
        # This should succeed but cause the validation endpoint to fail.
        assert res.status_code in {200, 201}, res.json()

        # validate the BC group "Group 1"
        res = client.get(f"/v1/studies/{study_id}/constraint-groups/Group 1/validate")
        assert res.status_code == 422, res.json()
        assert res.json()["exception"] == "MatrixWidthMismatchError"
        description = res.json()["description"]
        assert re.search(r"the most common width in the group is 3", description, flags=re.IGNORECASE)
        assert re.search(r"'third bc_lt' has 4 columns", description, flags=re.IGNORECASE)

        # first change `second_bc` operator to greater
        client.put(
            f"v1/studies/{study_id}/bindingconstraints/{second_bc_id}",
            json={"operator": "greater"},
        )

        # So, we correct the shape of the matrix of the Second BC
        res = client.put(
            f"/v1/studies/{study_id}/bindingconstraints/{second_bc_id}",
            json={"greater_term_matrix": matrix_lt3.tolist()},
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
        )
        assert res.status_code in {200, 201}, res.json()

        # validate the "Group 2": for the moment the BC is valid
        res = client.get(f"/v1/studies/{study_id}/constraint-groups/Group 2/validate")
        assert res.status_code in {200, 201}, res.json()

        res = client.put(
            f"v1/studies/{study_id}/bindingconstraints/{second_bc_id}",
            json={"greater_term_matrix": matrix_gt4.tolist()},
        )
        # This should succeed but cause the validation endpoint to fail.
        assert res.status_code in {200, 201}, res.json()

        # reset `second_bc` operator to less
        client.put(
            f"v1/studies/{study_id}/bindingconstraints/{second_bc_id}",
            json={"operator": "less"},
        )

        # Collect all the binding constraints groups
        res = client.get(f"/v1/studies/{study_id}/constraint-groups")
        assert res.status_code in {200, 201}, res.json()
        groups = res.json()
        assert set(groups) == {"default", "random_grp", "group 1", "group 2"}
        assert groups["group 2"] == [
            {
                "comments": "New API",
                "terms": [],
                "enabled": True,
                "filterSynthesis": "",
                "filterYearByYear": "",
                "group": "group 2",
                "id": "second bc",
                "name": "Second BC",
                "operator": "less",
                "timeStep": "hourly",
            }
        ]

        # Validate all binding constraints groups
        res = client.get(f"/v1/studies/{study_id}/constraint-groups/validate-all")
        assert res.status_code == 422, res.json()
        exception = res.json()["exception"]
        description = res.json()["description"]
        assert exception == "MatrixWidthMismatchError"
        assert re.search(r"'Group 1':", description, flags=re.IGNORECASE)
        assert re.search(r"the most common width in the group is 3", description, flags=re.IGNORECASE)
        assert re.search(r"'third bc_lt' has 4 columns", description, flags=re.IGNORECASE)

    @pytest.mark.parametrize("study_version", [870])
    @pytest.mark.parametrize("denormalize", [True, False])
    def test_rhs_matrices(
        self, client: TestClient, user_access_token: str, study_version: int, denormalize: bool
    ) -> None:
        """
        The goal of this test is to verify that there are no unnecessary RHS matrices created
        in the case of **creation** or **update** of a binding constraint.
        This test only concerns studies in **version >= 8.7** for which we have a specific matrix
        for each operation: "less", "equal", "greater" or "both".

        To perform this test, we will create a raw study "Base Study" with a "France" area
        and a single thermal cluster "Nuclear".
        We will then create a variant study "Variant Study" based on the raw study "Base Study"
        to apply binding constraint creation or update commands.

        The use of a variant and commands allows to check the behavior for both variant studies
        and raw studies by generating the variant snapshot.

        To verify the expected behaviors, we must control the number and naming of the matrices
        after generating the snapshot.
        In the case of an update and depending on the values of the `operator` and `time_step` parameters,
        we must also control the preservation or zeroing of the matrix values.
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}  # type: ignore

        # =======================
        #  RAW STUDY PREPARATION
        # =======================

        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("Base Study", version=study_version)
        area_id = preparer.create_area(study_id, name="France")["id"]
        cluster_id = preparer.create_thermal(study_id, area_id, name="Nuclear", group="Nuclear")["id"]

        # =============================
        # VARIANT STUDY CREATION
        # =============================

        variant_id = preparer.create_variant(study_id, name="Variant Study")

        # =============================
        #  CREATION W/O MATRICES
        # =============================

        all_time_steps = set(MATRIX_SIZES)
        all_operators = set(REQUIRED_MATRICES)

        for bc_time_step in all_time_steps:
            for bc_operator in all_operators:
                bc_name = f"BC_{bc_time_step}_{bc_operator}"
                # Creation of a binding constraint without matrices using a command
                res = client.post(
                    f"/v1/studies/{variant_id}/commands",
                    json=[
                        {
                            "action": "create_binding_constraint",
                            "args": {
                                "name": bc_name,
                                "type": bc_time_step,
                                "operator": bc_operator,
                                "coeffs": {f"{area_id}.{cluster_id.lower()}": [1, 2]},
                            },
                        }
                    ],
                )
                assert res.status_code == 200, res.json()

        preparer.generate_snapshot(variant_id, denormalize=denormalize)

        # Check the matrices size, values and existence
        for bc_time_step in all_time_steps:
            for bc_operator in all_operators:
                bc_name = f"BC_{bc_time_step}_{bc_operator}"
                bc_id = bc_name.lower()

                required_matrices = REQUIRED_MATRICES[bc_operator]
                for matrix in required_matrices:
                    df = preparer.download_matrix(variant_id, f"input/bindingconstraints/{bc_id}_{matrix}")
                    assert df.shape == (MATRIX_SIZES[bc_time_step], 1)
                    assert (df == 0).all().all()

                superfluous_matrices = {"lt", "gt", "eq"} - required_matrices
                for matrix in superfluous_matrices:
                    try:
                        preparer.download_matrix(variant_id, f"input/bindingconstraints/{bc_id}_{matrix}")
                    except HTTPError as e:
                        assert e.response.status_code == 404
                    else:
                        assert False, "The matrix should not exist"

        # drop all commands to avoid conflicts with the next test
        preparer.drop_all_commands(variant_id)

        # =============================
        #  CREATION WITH MATRICES
        # =============================

        # random matrices
        matrices_by_time_steps = {
            time_step: np.random.rand(size, 1).astype(np.float64) for time_step, size in MATRIX_SIZES.items()
        }

        for bc_time_step in all_time_steps:
            for bc_operator in all_operators:
                bc_name = f"BC_{bc_time_step}_{bc_operator}"
                matrix = matrices_by_time_steps[bc_time_step].tolist()
                args = {
                    "name": bc_name,
                    "type": bc_time_step,
                    "operator": bc_operator,
                    "coeffs": {f"{area_id}.{cluster_id.lower()}": [1, 2]},
                }
                if bc_operator == "less":
                    args["lessTermMatrix"] = matrix
                elif bc_operator == "greater":
                    args["greaterTermMatrix"] = matrix
                elif bc_operator == "equal":
                    args["equalTermMatrix"] = matrix
                else:
                    args["lessTermMatrix"] = args["greaterTermMatrix"] = matrix
                res = client.post(
                    f"/v1/studies/{variant_id}/commands",
                    json=[{"action": "create_binding_constraint", "args": args}],
                )
                assert res.status_code == 200, res.json()

        preparer.generate_snapshot(variant_id, denormalize=denormalize)

        # Check the matrices size, values and existence
        for bc_time_step in all_time_steps:
            for bc_operator in all_operators:
                bc_name = f"BC_{bc_time_step}_{bc_operator}"
                bc_id = bc_name.lower()

                required_matrices = REQUIRED_MATRICES[bc_operator]
                for matrix in required_matrices:
                    df = preparer.download_matrix(variant_id, f"input/bindingconstraints/{bc_id}_{matrix}")
                    assert df.shape == (MATRIX_SIZES[bc_time_step], 1)
                    assert np.allclose(df.values, matrices_by_time_steps[bc_time_step], atol=1e-6)

                superfluous_matrices = {"lt", "gt", "eq"} - required_matrices
                for matrix in superfluous_matrices:
                    try:
                        preparer.download_matrix(variant_id, f"input/bindingconstraints/{bc_id}_{matrix}")
                    except HTTPError as e:
                        assert e.response.status_code == 404
                    else:
                        assert False, "The matrix should not exist"
