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

        # Get the schema of the areas table
        res = client.get(
            "/v1/table-schema/areas",
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        assert set(actual["properties"]) == {
            # UI
            "colorRgb",
            # Optimization - Nodal optimization
            "nonDispatchablePower",
            "dispatchableHydroPower",
            "otherDispatchablePower",
            "averageUnsuppliedEnergyCost",
            "spreadUnsuppliedEnergyCost",
            "averageSpilledEnergyCost",
            "spreadSpilledEnergyCost",
            # Optimization - Filtering
            "filterSynthesis",
            "filterYearByYear",
            # Adequacy patch
            "adequacyPatchMode",
        }

        res = client.put(
            f"/v1/studies/{study_id}/table-mode/areas",
            headers=user_headers,
            json={
                "de": {
                    "averageUnsuppliedEnergyCost": 3456,
                    "dispatchableHydroPower": False,
                    "filterSynthesis": "daily, monthly",  # not changed
                    "filterYearByYear": "annual, weekly",
                },
                "es": {
                    "adequacyPatchMode": "inside",
                    "spreadSpilledEnergyCost": None,  # not changed
                },
                "fr": {
                    "colorRgb": "#C00000",
                },
            },
        )
        assert res.status_code == 200, res.json()
        expected_areas = {
            "de": {
                "adequacyPatchMode": "outside",
                "averageSpilledEnergyCost": 0,
                "averageUnsuppliedEnergyCost": 3456,
                "colorRgb": "#0080FF",
                "dispatchableHydroPower": False,
                "filterSynthesis": "daily, monthly",
                "filterYearByYear": "weekly, annual",
                "nonDispatchablePower": True,
                "otherDispatchablePower": True,
                "spreadSpilledEnergyCost": 0,
                "spreadUnsuppliedEnergyCost": 0,
            },
            "es": {
                "adequacyPatchMode": "inside",
                "averageSpilledEnergyCost": 0,
                "averageUnsuppliedEnergyCost": 3000,
                "colorRgb": "#0080FF",
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
                "colorRgb": "#C00000",
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
                "colorRgb": "#0080FF",
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
        assert actual == expected_areas

        res = client.get(f"/v1/studies/{study_id}/table-mode/areas", headers=user_headers)
        assert res.status_code == 200, res.json()
        actual = res.json()
        assert actual == expected_areas

        # Table Mode - Links
        # ==================

        # Get the schema of the links table
        res = client.get(
            "/v1/table-schema/links",
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        assert set(actual["properties"]) == {
            "colorRgb",
            "comments",
            "hurdlesCost",
            "loopFlow",
            "usePhaseShifter",
            "transmissionCapacities",
            "assetType",
            "linkStyle",
            "linkWidth",
            "displayComments",
            "filterSynthesis",
            "filterYearByYear",
        }

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
                    "comments": "Link from France to Italie",
                    "assetType": "DC",  # case-insensitive
                },
            },
        )
        assert res.status_code == 200, res.json()
        expected_links = {
            "de / fr": {
                "assetType": "ac",
                "colorRgb": "#FFA500",
                "comments": "",
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
                "comments": "",
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
                "comments": "Link from France to Italie",
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

        # Get the schema of the thermals table
        res = client.get(
            "/v1/table-schema/thermals",
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        assert set(actual["properties"]) == {
            # read-only fields
            "id",
            "name",
            # Thermals fields
            "group",
            "enabled",
            "unitCount",
            "nominalCapacity",
            "genTs",
            "minStablePower",
            "minUpTime",
            "minDownTime",
            "mustRun",
            "spinning",
            "volatilityForced",
            "volatilityPlanned",
            "lawForced",
            "lawPlanned",
            "marginalCost",
            "spreadCost",
            "fixedCost",
            "startupCost",
            "marketBidCost",
            # pollutants - since v8.6 (except for "co2")
            "co2",
            "nh3",
            "so2",
            "nox",
            "pm25",
            "pm5",
            "pm10",
            "nmvoc",
            "op1",
            "op2",
            "op3",
            "op4",
            "op5",
            # since v8.7
            "costGeneration",
            "efficiency",
            "variableOMCost",
        }

        res = client.put(
            f"/v1/studies/{study_id}/table-mode/thermals",
            headers=user_headers,
            json={
                "de / 01_solar": {
                    "group": "Other 2",
                    "nominalCapacity": 500000,
                    "so2": 8.25,
                    "unitCount": 17,
                },
                "de / 02_wind_on": {
                    "group": "Nuclear",
                    "nominalCapacity": 314159,
                    "co2": 123,
                    "unitCount": 15,
                },
            },
        )
        assert res.status_code == 200, res.json()
        expected_thermals = {
            "de / 01_solar": {
                # "id": "01_solar",
                # "name": "01_solar",
                "co2": 0,
                "costGeneration": None,
                "efficiency": None,
                "enabled": True,
                "fixedCost": 0,
                "genTs": "use global",
                "group": "Other 2",
                "lawForced": "uniform",
                "lawPlanned": "uniform",
                "marginalCost": 10,
                "marketBidCost": 10,
                "minDownTime": 1,
                "minStablePower": 0,
                "minUpTime": 1,
                "mustRun": False,
                "nh3": 0,
                "nmvoc": 0,
                "nominalCapacity": 500000,
                "nox": 0,
                "op1": 0,
                "op2": 0,
                "op3": 0,
                "op4": 0,
                "op5": 0,
                "pm10": 0,
                "pm25": 0,
                "pm5": 0,
                "so2": 8.25,
                "spinning": 0,
                "spreadCost": 0,
                "startupCost": 0,
                "unitCount": 17,
                "variableOMCost": None,
                "volatilityForced": 0,
                "volatilityPlanned": 0,
            },
            "de / 02_wind_on": {
                # "id": "02_wind_on",
                # "name": "02_wind_on",
                "co2": 123,
                "costGeneration": None,
                "efficiency": None,
                "enabled": True,
                "fixedCost": 0,
                "genTs": "use global",
                "group": "Nuclear",
                "lawForced": "uniform",
                "lawPlanned": "uniform",
                "marginalCost": 20,
                "marketBidCost": 20,
                "minDownTime": 1,
                "minStablePower": 0,
                "minUpTime": 1,
                "mustRun": False,
                "nh3": 0,
                "nmvoc": 0,
                "nominalCapacity": 314159,
                "nox": 0,
                "op1": 0,
                "op2": 0,
                "op3": 0,
                "op4": 0,
                "op5": 0,
                "pm10": 0,
                "pm25": 0,
                "pm5": 0,
                "so2": 0,
                "spinning": 0,
                "spreadCost": 0,
                "startupCost": 0,
                "unitCount": 15,
                "variableOMCost": None,
                "volatilityForced": 0,
                "volatilityPlanned": 0,
            },
        }
        assert res.json()["de / 01_solar"] == expected_thermals["de / 01_solar"]
        assert res.json()["de / 02_wind_on"] == expected_thermals["de / 02_wind_on"]

        res = client.get(
            f"/v1/studies/{study_id}/table-mode/thermals",
            headers=user_headers,
            params={"columns": ",".join(["group", "unitCount", "nominalCapacity", "so2"])},
        )
        assert res.status_code == 200, res.json()
        expected = {
            "de / 01_solar": {"group": "Other 2", "nominalCapacity": 500000, "so2": 8.25, "unitCount": 17},
            "de / 02_wind_on": {"group": "Nuclear", "nominalCapacity": 314159, "so2": 0, "unitCount": 15},
            "de / 03_wind_off": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "de / 04_res": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "de / 05_nuclear": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "de / 06_coal": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "de / 07_gas": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "de / 08_non-res": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "de / 09_hydro_pump": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "es / 01_solar": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "es / 02_wind_on": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "es / 03_wind_off": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "es / 04_res": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "es / 05_nuclear": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "es / 06_coal": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "es / 07_gas": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "es / 08_non-res": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "es / 09_hydro_pump": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "fr / 01_solar": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "fr / 02_wind_on": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "fr / 03_wind_off": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "fr / 04_res": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "fr / 05_nuclear": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "fr / 06_coal": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "fr / 07_gas": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "fr / 08_non-res": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "fr / 09_hydro_pump": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "it / 01_solar": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "it / 02_wind_on": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "it / 03_wind_off": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "it / 04_res": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "it / 05_nuclear": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "it / 06_coal": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "it / 07_gas": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "it / 08_non-res": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
            "it / 09_hydro_pump": {"group": "Other 1", "nominalCapacity": 1000000, "so2": 0, "unitCount": 1},
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

        # Get the schema of the renewables table
        res = client.get(
            "/v1/table-schema/renewables",
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        assert set(actual["properties"]) == {
            # read-only fields
            "id",
            "name",
            # Renewables fields
            "group",
            "tsInterpretation",
            "enabled",
            "unitCount",
            "nominalCapacity",
        }

        # Update some generators using the table mode
        res = client.put(
            f"/v1/studies/{study_id}/table-mode/renewables",
            headers=user_headers,
            json={
                "fr / Dieppe": {"enabled": False},
                "fr / La Rochelle": {"enabled": True, "nominalCapacity": 3.1, "unitCount": 2},
                "it / Pouilles": {"group": "Wind Onshore"},
            },
        )
        assert res.status_code == 200, res.json()

        res = client.get(
            f"/v1/studies/{study_id}/table-mode/renewables",
            headers=user_headers,
            params={"columns": ",".join(["group", "enabled", "unitCount", "nominalCapacity"])},
        )
        assert res.status_code == 200, res.json()
        expected = {
            "fr / Dieppe": {"enabled": False, "group": "Wind Offshore", "nominalCapacity": 8, "unitCount": 62},
            "fr / La Rochelle": {"enabled": True, "group": "Solar PV", "nominalCapacity": 3.1, "unitCount": 2},
            "fr / Oleron": {"enabled": True, "group": "Wind Offshore", "nominalCapacity": 15, "unitCount": 70},
            "it / Pouilles": {"enabled": False, "group": "Wind Onshore", "nominalCapacity": 11, "unitCount": 40},
            "it / Sardaigne": {"enabled": True, "group": "Wind Offshore", "nominalCapacity": 12, "unitCount": 86},
            "it / Sicile": {"enabled": True, "group": "Solar PV", "nominalCapacity": 1.8, "unitCount": 1},
        }
        actual = res.json()
        assert actual == expected

        # Table Mode - Short Term Storage
        # ===============================

        # Get the schema of the short-term storages table
        res = client.get(
            "/v1/table-schema/st-storages",
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        assert set(actual["properties"]) == {
            # read-only fields
            "id",
            "name",
            # Short-term storage fields
            "group",
            "injectionNominalCapacity",
            "withdrawalNominalCapacity",
            "reservoirCapacity",
            "efficiency",
            "initialLevel",
            "initialLevelOptim",
        }

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

        # Update some generators using the table mode
        res = client.put(
            f"/v1/studies/{study_id}/table-mode/st-storages",
            headers=user_headers,
            json={
                "fr / siemens": {"injectionNominalCapacity": 1550, "withdrawalNominalCapacity": 1550},
                "fr / tesla": {"efficiency": 0.75, "initialLevel": 0.89, "initialLevelOptim": False},
                "it / storage3": {"group": "Pondage"},
            },
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        assert actual == {
            "fr / siemens": {
                # "id": "siemens",
                # "name": "Siemens",
                "efficiency": 1,
                "group": "Battery",
                "initialLevel": 0.5,
                "initialLevelOptim": False,
                "injectionNominalCapacity": 1550,
                "reservoirCapacity": 1500,
                "withdrawalNominalCapacity": 1550,
            },
            "fr / tesla": {
                # "id": "tesla",
                # "name": "Tesla",
                "efficiency": 0.75,
                "group": "Battery",
                "initialLevel": 0.89,
                "initialLevelOptim": False,
                "injectionNominalCapacity": 1200,
                "reservoirCapacity": 1200,
                "withdrawalNominalCapacity": 1200,
            },
            "it / storage3": {
                # "id": "storage3",
                # "name": "storage3",
                "efficiency": 1,
                "group": "Pondage",
                "initialLevel": 1,
                "initialLevelOptim": False,
                "injectionNominalCapacity": 1234,
                "reservoirCapacity": 1357,
                "withdrawalNominalCapacity": 1020,
            },
            "it / storage4": {
                # "id": "storage4",
                # "name": "storage4",
                "efficiency": 1,
                "group": "PSP_open",
                "initialLevel": 0.5,
                "initialLevelOptim": True,
                "injectionNominalCapacity": 567,
                "reservoirCapacity": 500,
                "withdrawalNominalCapacity": 456,
            },
        }

        res = client.get(
            f"/v1/studies/{study_id}/table-mode/st-storages",
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
                "injectionNominalCapacity": 1550,
                "reservoirCapacity": 1500,
                "unknowColumn": None,
                "withdrawalNominalCapacity": 1550,
            },
            "fr / tesla": {
                "group": "Battery",
                "injectionNominalCapacity": 1200,
                "reservoirCapacity": 1200,
                "unknowColumn": None,
                "withdrawalNominalCapacity": 1200,
            },
            "it / storage3": {
                "group": "Pondage",
                "injectionNominalCapacity": 1234,
                "reservoirCapacity": 1357,
                "unknowColumn": None,
                "withdrawalNominalCapacity": 1020,
            },
            "it / storage4": {
                "group": "PSP_open",
                "injectionNominalCapacity": 567,
                "reservoirCapacity": 500,
                "unknowColumn": None,
                "withdrawalNominalCapacity": 456,
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

        # Get the schema of the binding constraints table
        res = client.get(
            "/v1/table-schema/binding-constraints",
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        assert set(actual["properties"]) == {
            # read-only fields
            "id",
            "name",
            # Binding Constraints fields
            "group",
            "enabled",
            "timeStep",
            "operator",
            "comments",
            "filterSynthesis",
            "filterYearByYear",
            # Binding Constraints - Terms
            "terms",
        }

        # Update some binding constraints using the table mode
        res = client.put(
            f"/v1/studies/{study_id}/table-mode/binding-constraints",
            headers=user_headers,
            json={
                "binding constraint 1": {"comments": "Hello World!", "enabled": True},
                "binding constraint 2": {"filterSynthesis": "hourly", "filterYearByYear": "hourly", "operator": "both"},
            },
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        assert actual == {
            "binding constraint 1": {
                "comments": "Hello World!",
                "enabled": True,
                "filterSynthesis": "",
                "filterYearByYear": "",
                "operator": "less",
                "timeStep": "hourly",
            },
            "binding constraint 2": {
                "comments": "This is a binding constraint",
                "enabled": False,
                "filterSynthesis": "hourly",
                "filterYearByYear": "hourly",
                "operator": "both",
                "timeStep": "daily",
            },
        }

        res = client.get(
            f"/v1/studies/{study_id}/table-mode/binding-constraints",
            headers=user_headers,
            params={"columns": ""},
        )
        assert res.status_code == 200, res.json()
        expected = {
            "binding constraint 1": {
                "comments": "Hello World!",
                "enabled": True,
                "filterSynthesis": "",
                "filterYearByYear": "",
                "operator": "less",
                "timeStep": "hourly",
            },
            "binding constraint 2": {
                "comments": "This is a binding constraint",
                "enabled": False,
                "filterSynthesis": "hourly",
                "filterYearByYear": "hourly",
                "operator": "both",
                "timeStep": "daily",
            },
        }
        actual = res.json()
        assert actual == expected
