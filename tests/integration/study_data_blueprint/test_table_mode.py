import pytest
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from tests.integration.utils import wait_task_completion


# noinspection SpellCheckingInspection
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
        user_headers = {"Authorization": f"Bearer {user_access_token}"}

        # In order to test the table mode for renewable clusters and short-term storage,
        # it is required that the study is either in version 8.1 for renewable energies
        # or in version 8.6 for short-term storage and that the renewable clusters are enabled
        # in the study configuration.

        # Upgrade the study to version 8.6
        res = client.put(
            f"/v1/studies/{study_id}/upgrade",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"target_version": 860},
        )
        assert res.status_code == 200, res.json()

        task_id = res.json()
        task = wait_task_completion(client, user_access_token, task_id)
        assert task.status == TaskStatus.COMPLETED, task

        # Parameter 'renewable-generation-modelling' must be set to 'clusters' instead of 'aggregated'.
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
        assert res.status_code == 200, res.json()

        # Table Mode - Area
        # =================

        # res = client.put(
        #     f"/v1/studies/{study_id}/table-mode/areas",
        #     headers=user_headers,
        #     json={
        #         "de": {
        #             "averageUnsuppliedEnergyCost": 3456,
        #             "dispatchableHydroPower": False,
        #             "filterSynthesis": "daily, monthly",
        #             "filterYearByYear": "weekly, annual",
        #         },
        #         "es": {
        #             "adequacyPatchMode": "inside",
        #             "spreadSpilledEnergyCost": None,  # not changed
        #         },
        #     },
        # )
        # assert res.status_code == 200, res.json()

        res = client.get(f"/v1/studies/{study_id}/table-mode/areas", headers=user_headers)
        assert res.status_code == 200, res.json()
        expected = {
            "de": {
                "adequacyPatchMode": "outside",
                "averageSpilledEnergyCost": 0,
                "averageUnsuppliedEnergyCost": 3000,
                "dispatchableHydroPower": True,
                "filterSynthesis": "daily, monthly",
                "filterYearByYear": "hourly, weekly, annual",
                "nonDispatchablePower": True,
                "otherDispatchablePower": True,
                "spreadSpilledEnergyCost": 0,
                "spreadUnsuppliedEnergyCost": 0,
            },
            "es": {
                "adequacyPatchMode": "outside",
                "averageSpilledEnergyCost": 0,
                "averageUnsuppliedEnergyCost": 3000,
                "dispatchableHydroPower": True,
                "filterSynthesis": "daily, monthly",
                "filterYearByYear": "hourly, weekly, annual",
                "nonDispatchablePower": True,
                "otherDispatchablePower": True,
                "spreadSpilledEnergyCost": 0,
                "spreadUnsuppliedEnergyCost": 0,
            },
            "fr": {
                "adequacyPatchMode": "outside",
                "averageSpilledEnergyCost": 0,
                "averageUnsuppliedEnergyCost": 3000,
                "dispatchableHydroPower": True,
                "filterSynthesis": "",
                "filterYearByYear": "hourly",
                "nonDispatchablePower": True,
                "otherDispatchablePower": True,
                "spreadSpilledEnergyCost": 0,
                "spreadUnsuppliedEnergyCost": 0,
            },
            "it": {
                "adequacyPatchMode": "outside",
                "averageSpilledEnergyCost": 0,
                "averageUnsuppliedEnergyCost": 3000,
                "dispatchableHydroPower": True,
                "filterSynthesis": "",
                "filterYearByYear": "hourly",
                "nonDispatchablePower": True,
                "otherDispatchablePower": True,
                "spreadSpilledEnergyCost": 0,
                "spreadUnsuppliedEnergyCost": 0,
            },
        }
        actual = res.json()
        assert actual == expected

        # Table Mode - Links
        # ==================

        res = client.put(
            f"/v1/studies/{study_id}/table-mode/links",
            headers=user_headers,
            json={
                "de / fr": {
                    "colorRgb": "#FFA500",
                    "displayComments": False,
                    "filterSynthesis": "hourly, daily, weekly, annual",
                    "filterYearByYear": "hourly, daily, monthly, annual",
                    "hurdlesCost": True,
                    "linkStyle": "plain",
                    "linkWidth": 2,
                    "loopFlow": False,
                    "transmissionCapacities": "ignore",
                },
                "es / fr": {
                    "colorRgb": "#FF6347",
                    "displayComments": True,
                    "filterSynthesis": "hourly, daily, weekly, monthly, annual, annual",  # duplicate is ignored
                    "filterYearByYear": "hourly, daily, weekly, annual",
                    "hurdlesCost": True,
                    "linkStyle": "plain",
                    "linkWidth": 1,
                    "loopFlow": False,
                    "transmissionCapacities": "enabled",
                    "usePhaseShifter": True,
                },
                "fr / it": {
                    "assetType": "DC",  # case-insensitive
                },
            },
        )
        assert res.status_code == 200, res.json()
        expected_links = {
            "de / fr": {
                "assetType": "ac",
                "colorRgb": "#FFA500",
                "displayComments": False,
                "filterSynthesis": "hourly, daily, weekly, annual",
                "filterYearByYear": "hourly, daily, monthly, annual",
                "hurdlesCost": True,
                "linkStyle": "plain",
                "linkWidth": 2,
                "loopFlow": False,
                "transmissionCapacities": "ignore",
                "usePhaseShifter": False,
            },
            "es / fr": {
                "assetType": "ac",
                "colorRgb": "#FF6347",
                "displayComments": True,
                "filterSynthesis": "hourly, daily, weekly, monthly, annual",
                "filterYearByYear": "hourly, daily, weekly, annual",
                "hurdlesCost": True,
                "linkStyle": "plain",
                "linkWidth": 1,
                "loopFlow": False,
                "transmissionCapacities": "enabled",
                "usePhaseShifter": True,
            },
            "fr / it": {
                "assetType": "dc",
                "colorRgb": "#707070",
                "displayComments": True,
                "filterSynthesis": "",
                "filterYearByYear": "hourly",
                "hurdlesCost": True,
                "linkStyle": "plain",
                "linkWidth": 1,
                "loopFlow": False,
                "transmissionCapacities": "enabled",
                "usePhaseShifter": False,
            },
        }
        actual = res.json()
        assert actual == expected_links

        res = client.get(f"/v1/studies/{study_id}/table-mode/links", headers=user_headers)
        assert res.status_code == 200, res.json()
        actual = res.json()
        assert actual == expected_links

        # Table Mode - Thermal Clusters
        # =============================

        res = client.get(
            f"/v1/studies/{study_id}/table-mode/thermals",
            headers=user_headers,
            params={"columns": ",".join(["group", "unitCount", "nominalCapacity", "so2"])},
        )
        assert res.status_code == 200, res.json()
        expected = {
            "de / 01_solar": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "de / 02_wind_on": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "de / 03_wind_off": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "de / 04_res": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "de / 05_nuclear": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "de / 06_coal": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "de / 07_gas": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "de / 08_non-res": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "de / 09_hydro_pump": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "es / 01_solar": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "es / 02_wind_on": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "es / 03_wind_off": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "es / 04_res": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "es / 05_nuclear": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "es / 06_coal": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "es / 07_gas": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "es / 08_non-res": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "es / 09_hydro_pump": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "fr / 01_solar": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "fr / 02_wind_on": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "fr / 03_wind_off": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "fr / 04_res": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "fr / 05_nuclear": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "fr / 06_coal": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "fr / 07_gas": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "fr / 08_non-res": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "fr / 09_hydro_pump": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "it / 01_solar": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "it / 02_wind_on": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "it / 03_wind_off": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "it / 04_res": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "it / 05_nuclear": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "it / 06_coal": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "it / 07_gas": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "it / 08_non-res": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
            "it / 09_hydro_pump": {"group": "Other 1", "nominalCapacity": 1000000.0, "so2": 0.0, "unitCount": 1},
        }
        actual = res.json()
        assert actual == expected

        # Table Mode - Renewable Clusters
        # ===============================

        # Prepare data for renewable clusters tests
        generators_by_country = {
            "fr": {
                "La Rochelle": {
                    "name": "La Rochelle",
                    "group": "solar pv",
                    "nominalCapacity": 2.1,
                    "unitCount": 1,
                    "tsInterpretation": "production-factor",
                },
                "Oleron": {
                    "name": "Oleron",
                    "group": "wind offshore",
                    "nominalCapacity": 15,
                    "unitCount": 70,
                    "tsInterpretation": "production-factor",
                },
                "Dieppe": {
                    "name": "Dieppe",
                    "group": "wind offshore",
                    "nominalCapacity": 8,
                    "unitCount": 62,
                    "tsInterpretation": "power-generation",
                },
            },
            "it": {
                "Sicile": {
                    "name": "Sicile",
                    "group": "solar pv",
                    "nominalCapacity": 1.8,
                    "unitCount": 1,
                    "tsInterpretation": "production-factor",
                },
                "Sardaigne": {
                    "name": "Sardaigne",
                    "group": "wind offshore",
                    "nominalCapacity": 12,
                    "unitCount": 86,
                    "tsInterpretation": "power-generation",
                },
                "Pouilles": {
                    "name": "Pouilles",
                    "enabled": False,
                    "group": "wind offshore",
                    "nominalCapacity": 11,
                    "unitCount": 40,
                    "tsInterpretation": "power-generation",
                },
            },
        }

        for area_id, generators in generators_by_country.items():
            for generator_id, generator in generators.items():
                res = client.post(
                    f"/v1/studies/{study_id}/areas/{area_id}/clusters/renewable",
                    headers=user_headers,
                    json=generator,
                )
                res.raise_for_status()

        res = client.get(
            f"/v1/studies/{study_id}/table-mode/renewables",
            headers=user_headers,
            params={"columns": ",".join(["group", "enabled", "unitCount", "nominalCapacity"])},
        )
        assert res.status_code == 200, res.json()
        expected = {
            "fr / Dieppe": {"enabled": True, "group": "Wind Offshore", "nominalCapacity": 8, "unitCount": 62},
            "fr / La Rochelle": {"enabled": True, "group": "Solar PV", "nominalCapacity": 2.1, "unitCount": 1},
            "fr / Oleron": {"enabled": True, "group": "Wind Offshore", "nominalCapacity": 15, "unitCount": 70},
            "it / Pouilles": {"enabled": False, "group": "Wind Offshore", "nominalCapacity": 11, "unitCount": 40},
            "it / Sardaigne": {"enabled": True, "group": "Wind Offshore", "nominalCapacity": 12, "unitCount": 86},
            "it / Sicile": {"enabled": True, "group": "Solar PV", "nominalCapacity": 1.8, "unitCount": 1},
        }
        actual = res.json()
        assert actual == expected

        # Table Mode - Short Term Storage
        # ===============================

        # Prepare data for short-term storage tests
        storage_by_country = {
            "fr": {
                "siemens": {
                    "name": "Siemens",
                    "group": "battery",
                    "injectionNominalCapacity": 1500,
                    "withdrawalNominalCapacity": 1500,
                    "reservoirCapacity": 1500,
                    "initialLevel": 0.5,
                    "initialLevelOptim": False,
                },
                "tesla": {
                    "name": "Tesla",
                    "group": "battery",
                    "injectionNominalCapacity": 1200,
                    "withdrawalNominalCapacity": 1200,
                    "reservoirCapacity": 1200,
                    "initialLevelOptim": True,
                },
            },
            "it": {
                "storage3": {
                    "name": "storage3",
                    "group": "psp_open",
                    "injectionNominalCapacity": 1234,
                    "withdrawalNominalCapacity": 1020,
                    "reservoirCapacity": 1357,
                    "initialLevel": 1,
                    "initialLevelOptim": False,
                },
                "storage4": {
                    "name": "storage4",
                    "group": "psp_open",
                    "injectionNominalCapacity": 567,
                    "withdrawalNominalCapacity": 456,
                    "reservoirCapacity": 500,
                    "initialLevelOptim": True,
                },
            },
        }
        for area_id, storages in storage_by_country.items():
            for storage_id, storage in storages.items():
                res = client.post(
                    f"/v1/studies/{study_id}/areas/{area_id}/storages",
                    headers=user_headers,
                    json=storage,
                )
                res.raise_for_status()

        res = client.get(
            f"/v1/studies/{study_id}/table-mode/storages",
            headers=user_headers,
            params={
                "columns": ",".join(
                    [
                        "group",
                        "injectionNominalCapacity",
                        "withdrawalNominalCapacity",
                        "reservoirCapacity",
                        "unknowColumn",
                    ]
                ),
            },
        )
        assert res.status_code == 200, res.json()
        expected = {
            "fr / siemens": {
                "group": "Battery",
                "injectionNominalCapacity": 1500,
                "reservoirCapacity": 1500,
                "withdrawalNominalCapacity": 1500,
                "unknowColumn": None,
            },
            "fr / tesla": {
                "group": "Battery",
                "injectionNominalCapacity": 1200,
                "reservoirCapacity": 1200,
                "withdrawalNominalCapacity": 1200,
                "unknowColumn": None,
            },
            "it / storage3": {
                "group": "PSP_open",
                "injectionNominalCapacity": 1234,
                "reservoirCapacity": 1357,
                "withdrawalNominalCapacity": 1020,
                "unknowColumn": None,
            },
            "it / storage4": {
                "group": "PSP_open",
                "injectionNominalCapacity": 567,
                "reservoirCapacity": 500,
                "withdrawalNominalCapacity": 456,
                "unknowColumn": None,
            },
        }
        actual = res.json()
        assert actual == expected

        # Table Mode - Binding Constraints
        # ================================

        # Prepare data for binding constraints tests
        # Create a cluster in fr
        fr_id = "fr"
        res = client.post(
            f"/v1/studies/{study_id}/areas/{fr_id}/clusters/thermal",
            headers=user_headers,
            json={
                "name": "Cluster 1",
                "group": "Nuclear",
            },
        )
        assert res.status_code == 200, res.json()
        cluster_id = res.json()["id"]
        assert cluster_id == "Cluster 1"

        # Create Binding Constraints
        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={
                "name": "Binding Constraint 1",
                "enabled": True,
                "time_step": "hourly",
                "operator": "less",
            },
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()

        res = client.post(
            f"/v1/studies/{study_id}/bindingconstraints",
            json={
                "name": "Binding Constraint 2",
                "enabled": False,
                "time_step": "daily",
                "operator": "greater",
                "comments": "This is a binding constraint",
                "filter_synthesis": "hourly, daily, weekly",
            },
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()

        res = client.get(
            f"/v1/studies/{study_id}/table-mode/constraints",
            headers=user_headers,
            params={"columns": ""},
        )
        assert res.status_code == 200, res.json()
        expected = {
            "binding constraint 1": {
                "comments": "",
                "enabled": True,
                "filterSynthesis": "",
                "filterYearByYear": "",
                "operator": "less",
                "timeStep": "hourly",
            },
            "binding constraint 2": {
                "comments": "This is a binding constraint",
                "enabled": False,
                "filterSynthesis": "hourly, daily, weekly",
                "filterYearByYear": "",
                "operator": "greater",
                "timeStep": "daily",
            },
        }
        actual = res.json()
        assert actual == expected
