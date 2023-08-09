import http

import numpy as np
import pytest
from starlette.testclient import TestClient

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)


# noinspection SpellCheckingInspection
@pytest.mark.integration_test
class TestRenewableCluster:
    """
    This unit test is designed to demonstrate the creation, modification of properties and
    updating of matrices, and the deletion of one or more renewable cluster.
    """

    def test_lifecycle(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
    ) -> None:
        # sourcery skip: extract-duplicate-method

        # =====================
        #  General Data Update
        # =====================

        # The `enr_modelling` value must be set to "clusters" instead of "aggregated"
        args = {
            "target": "settings/generaldata/other preferences",
            "data": {"renewable-generation-modelling": "clusters"},
        }
        res = client.post(
            f"/v1/studies/{study_id}/commands",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[{"action": "update_config", "args": args}],
        )
        res.raise_for_status()

        # =================================
        #  Create Renewable Clusters in FR
        # =================================

        area_fr_id = transform_name_to_id("FR")

        cluster_fr1 = "Oleron"
        cluster_fr1_id = transform_name_to_id(cluster_fr1)
        args = {
            "area_id": area_fr_id,
            "cluster_name": cluster_fr1_id,
            "parameters": {
                "group": "wind offshore",
                "name": cluster_fr1,
                "ts-interpretation": "power-generation",
                "nominalcapacity": 2500,
            },
        }
        res = client.post(
            f"/v1/studies/{study_id}/commands",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[{"action": "create_renewables_cluster", "args": args}],
        )
        res.raise_for_status()

        cluster_fr2 = "La_Rochelle"
        cluster_fr2_id = transform_name_to_id(cluster_fr2)
        args = {
            "area_id": area_fr_id,
            "cluster_name": cluster_fr2_id,
            "parameters": {
                "group": "solar pv",
                "name": cluster_fr2,
                "ts-interpretation": "power-generation",
                "unitcount": 4,
                "enabled": False,
                "nominalcapacity": 3500,
            },
        }
        res = client.post(
            f"/v1/studies/{study_id}/commands",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[{"action": "create_renewables_cluster", "args": args}],
        )
        res.raise_for_status()

        # Check the properties of the renewable clusters in the "FR" area
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_fr_id}/clusters/renewable/{cluster_fr1_id}/form",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        properties = res.json()
        expected = {
            "enabled": True,
            "group": "wind offshore",
            "name": cluster_fr1_id,  # known bug: should be `cluster_fr1`
            "nominalCapacity": 2500.0,
            "tsInterpretation": "power-generation",
            "unitCount": 1,
        }
        assert properties == expected

        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_fr_id}/clusters/renewable/{cluster_fr2_id}/form",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        properties = res.json()
        expected = {
            "enabled": False,
            "group": "solar pv",
            "name": cluster_fr2_id,  # known bug: should be `cluster_fr2`
            "nominalCapacity": 3500.0,
            "tsInterpretation": "power-generation",
            "unitCount": 4,
        }
        assert properties == expected

        # ======================================
        #  Renewable Cluster Time Series Update
        # ======================================

        # Then, it is possible to update a time series.
        values_fr1 = np.random.randint(0, 1001, size=(8760, 1))
        args_fr1 = {
            "target": f"input/renewables/series/{area_fr_id}/{cluster_fr1_id}/series",
            "matrix": values_fr1.tolist(),
        }
        values_fr2 = np.random.randint(0, 1001, size=(8760, 1))
        args_fr2 = {
            "target": f"input/renewables/series/{area_fr_id}/{cluster_fr2_id}/series",
            "matrix": values_fr2.tolist(),
        }
        res = client.post(
            f"/v1/studies/{study_id}/commands",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[
                {"action": "replace_matrix", "args": args_fr1},
                {"action": "replace_matrix", "args": args_fr2},
            ],
        )
        res.raise_for_status()

        # Check the matrices of the renewable clusters in the "FR" area
        res = client.get(
            f"/v1/studies/{study_id}/raw?path=input/renewables/series/{area_fr_id}/{cluster_fr1_id}/series",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        matrix_fr1 = res.json()
        assert (
            np.array(matrix_fr1["data"], dtype=np.float64).all()
            == values_fr1.all()
        )

        res = client.get(
            f"/v1/studies/{study_id}/raw?path=input/renewables/series/{area_fr_id}/{cluster_fr2_id}/series",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        matrix_fr2 = res.json()
        assert (
            np.array(matrix_fr2["data"], dtype=np.float64).all()
            == values_fr2.all()
        )

        # =================================
        #  Create Renewable Clusters in IT
        # =================================

        area_it_id = transform_name_to_id("IT")

        cluster_it1 = "Oléron"
        cluster_it1_id = transform_name_to_id(cluster_it1)
        args = {
            "area_id": area_it_id,
            "cluster_name": cluster_it1_id,
            "parameters": {
                "group": "wind offshore",
                "name": cluster_it1,
                "unitcount": 1,
                "nominalcapacity": 1000,
                "ts-interpretation": "production-factor",
            },
        }
        res = client.post(
            f"/v1/studies/{study_id}/commands",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[{"action": "create_renewables_cluster", "args": args}],
        )
        res.raise_for_status()

        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_it_id}/clusters/renewable/{cluster_it1_id}/form",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        properties = res.json()
        expected = {
            "enabled": True,
            "group": "wind offshore",
            "name": cluster_it1_id,  # known bug: should be `cluster_it1`
            "nominalCapacity": 1000.0,
            "tsInterpretation": "production-factor",
            "unitCount": 1,
        }
        assert properties == expected

        # Check the matrices of the renewable clusters in the "IT" area
        res = client.get(
            f"/v1/studies/{study_id}/raw?path=input/renewables/series/{area_it_id}/{cluster_it1_id}/series",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        matrix_it1 = res.json()
        assert (
            np.array(matrix_it1["data"]).all()
            == np.zeros(shape=(8760, 1)).all()
        )

        # ===========================
        #  Renewable Cluster Removal
        # ===========================

        # The `remove_renewables_cluster` command allows you to delete a Renewable Cluster.
        args = {"area_id": area_fr_id, "cluster_id": cluster_fr2_id}
        res = client.post(
            f"/v1/studies/{study_id}/commands",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[{"action": "remove_renewables_cluster", "args": args}],
        )
        res.raise_for_status()

        # Check the properties of all renewable clusters
        res = client.get(
            f"/v1/studies/{study_id}/raw?path=input/renewables/clusters&depth=4",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        properties = res.json()
        assert properties == {
            "de": {"list": {}},
            "es": {"list": {}},
            "fr": {
                "list": {
                    cluster_fr1_id: {
                        "group": "wind offshore",
                        "name": cluster_fr1_id,
                        "nominalcapacity": 2500,
                        "ts-interpretation": "power-generation",
                    },
                }
            },
            "it": {
                "list": {
                    cluster_it1_id: {
                        "group": "wind offshore",
                        "name": cluster_it1_id,
                        "nominalcapacity": 1000,
                        "ts-interpretation": "production-factor",
                        "unitcount": 1,
                    }
                }
            },
        }

        # The `remove_renewables_cluster` command allows you to delete a Renewable Cluster.
        args = {"area_id": area_fr_id, "cluster_id": cluster_fr1_id}
        res = client.post(
            f"/v1/studies/{study_id}/commands",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[{"action": "remove_renewables_cluster", "args": args}],
        )
        res.raise_for_status()

        # Check the properties of all renewable clusters
        res = client.get(
            f"/v1/studies/{study_id}/raw?path=input/renewables/clusters&depth=4",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        res.raise_for_status()
        properties = res.json()
        assert properties == {
            "de": {"list": {}},
            "es": {"list": {}},
            "fr": {"list": {}},
            "it": {
                "list": {
                    cluster_it1_id: {
                        "group": "wind offshore",
                        "name": cluster_it1_id,
                        "nominalcapacity": 1000,
                        "ts-interpretation": "production-factor",
                        "unitcount": 1,
                    }
                }
            },
        }

        # If you try to delete a non-existent thermal cluster,
        # you should receive an HTTP 404 Not Found error. However,
        # this behavior is not yet implemented, so you will encounter a 500 error.
        args = {"area_id": area_fr_id, "cluster_id": cluster_fr2_id}
        res = client.post(
            f"/v1/studies/{study_id}/commands",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[{"action": "remove_renewables_cluster", "args": args}],
        )
        assert res.status_code == http.HTTPStatus.INTERNAL_SERVER_ERROR
        result = res.json()
        assert (
            "'la_rochelle' not a child of ClusteredRenewableClusterSeries"
            in result["description"]
        )
