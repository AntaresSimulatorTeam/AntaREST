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

import copy
import typing as t

import pytest
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from tests.integration.utils import wait_task_completion

# noinspection SpellCheckingInspection
POLLUTANTS_860 = ("nh3", "nmvoc", "nox", "op1", "op2", "op3", "op4", "op5", "pm10", "pm25", "pm5", "so2")


# noinspection SpellCheckingInspection
@pytest.mark.unit_test
class TestTableMode:
    """
    Test the end points related to the table mode.

    Those tests use the "examples/studies/STA-mini.zip" Study,
    which contains the following areas: ["de", "es", "fr", "it"].
    """

    @pytest.mark.parametrize("study_version", [0, 810, 830, 860, 870, 880])
    def test_lifecycle__nominal(
        self, client: TestClient, user_access_token: str, internal_study_id: str, study_version: int
    ) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # In order to test the table mode for renewable clusters and short-term storage,
        # it is required that the study is either in version 8.1 for renewable energies
        # or in version 8.6 for short-term storage and that the renewable clusters are enabled
        # in the study configuration.

        # Upgrade the study to the desired version
        if study_version:
            res = client.put(
                f"/v1/studies/{internal_study_id}/upgrade",
                params={"target_version": study_version},
            )
            assert res.status_code == 200, res.json()

            task_id = res.json()
            task = wait_task_completion(client, user_access_token, task_id)
            assert task.status == TaskStatus.COMPLETED, task

        # Create another link to test specific bug.
        res = client.post(f"/v1/studies/{internal_study_id}/links", json={"area1": "de", "area2": "it"})
        assert res.status_code in [200, 201], res.json()

        # Table Mode - Area
        # =================

        # Get the schema of the areas table
        res = client.get("/v1/table-schema/areas")
        assert res.status_code == 200, res.json()
        actual = res.json()
        assert set(actual["properties"]) == {
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

        _de_values = {
            "averageUnsuppliedEnergyCost": 3456,
            "dispatchableHydroPower": False,
            "filterSynthesis": "daily, monthly",  # not changed
            "filterYearByYear": "annual, weekly",
        }
        _es_values = {"spreadSpilledEnergyCost": None}  # not changed

        if study_version >= 830:
            _es_values["adequacyPatchMode"] = "inside"

        res = client.put(
            f"/v1/studies/{internal_study_id}/table-mode/areas",
            json={
                "de": _de_values,
                "es": _es_values,
            },
        )
        assert res.status_code == 200, res.json()
        expected_areas: t.Dict[str, t.Dict[str, t.Any]]
        expected_areas = {
            "de": {
                "averageSpilledEnergyCost": 0,
                "averageUnsuppliedEnergyCost": 3456,
                "dispatchableHydroPower": False,
                "filterSynthesis": "daily, monthly",
                "filterYearByYear": "weekly, annual",
                "nonDispatchablePower": True,
                "otherDispatchablePower": True,
                "spreadSpilledEnergyCost": 0,
                "spreadUnsuppliedEnergyCost": 0,
            },
            "es": {
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

        if study_version >= 830:
            expected_areas["de"]["adequacyPatchMode"] = "outside"
            expected_areas["es"]["adequacyPatchMode"] = "inside"
            expected_areas["fr"]["adequacyPatchMode"] = "outside"
            expected_areas["it"]["adequacyPatchMode"] = "outside"

        actual = res.json()
        assert actual == expected_areas

        res = client.get(f"/v1/studies/{internal_study_id}/table-mode/areas")
        assert res.status_code == 200, res.json()
        actual = res.json()
        assert actual == expected_areas

        # Specific tests for averageSpilledEnergyCost and averageUnsuppliedEnergyCost
        _de_values = {
            "averageSpilledEnergyCost": 123,
            "averageUnsuppliedEnergyCost": 456,
        }
        res = client.put(
            f"/v1/studies/{internal_study_id}/table-mode/areas",
            json={"de": _de_values},
        )
        assert res.status_code == 200, res.json()
        actual = res.json()["de"]
        assert actual["averageSpilledEnergyCost"] == 123
        assert actual["averageUnsuppliedEnergyCost"] == 456

        # Table Mode - Links
        # ==================

        # Get the schema of the links table
        res = client.get(
            "/v1/table-schema/links",
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        assert set(actual["properties"]) == {
            "assetType",
            "colorb",
            "colorg",
            "colorr",
            "displayComments",
            "comments",
            "filterSynthesis",
            "filterYearByYear",
            "hurdlesCost",
            "linkStyle",
            "linkWidth",
            "loopFlow",
            "transmissionCapacities",
            "usePhaseShifter",
        }

        # Test links

        json_input = {
            "de / fr": {
                "assetType": "ac",
                "colorb": 100,
                "colorg": 150,
                "colorr": 200,
                "displayComments": False,
                "hurdlesCost": True,
                "linkStyle": "plain",
                "linkWidth": 2,
                "loopFlow": False,
                "transmissionCapacities": "ignore",
                "filterSynthesis": "hourly",
                "filterYearByYear": "annual",
            },
            "es / fr": {
                "assetType": "ac",
                "colorb": 100,
                "colorg": 150,
                "colorr": 200,
                "displayComments": True,
                "hurdlesCost": True,
                "linkStyle": "plain",
                "linkWidth": 1,
                "loopFlow": False,
                "transmissionCapacities": "enabled",
                "usePhaseShifter": True,
                "filterSynthesis": "monthly",
                "filterYearByYear": "weekly",
            },
            "fr / it": {
                "assetType": "dc",  # case-insensitive
            },
        }

        expected_links = {
            "de / fr": {
                "area1": "de",
                "area2": "fr",
                "assetType": "ac",
                "colorb": 100,
                "colorg": 150,
                "colorr": 200,
                "displayComments": False,
                "comments": "",
                "hurdlesCost": True,
                "linkStyle": "plain",
                "linkWidth": 2,
                "loopFlow": False,
                "transmissionCapacities": "ignore",
                "usePhaseShifter": False,
                "filterSynthesis": "hourly",
                "filterYearByYear": "annual",
            },
            "de / it": {
                "area1": "de",
                "area2": "it",
                "assetType": "ac",
                "colorr": 112,
                "colorg": 112,
                "colorb": 112,
                "displayComments": True,
                "comments": "",
                "hurdlesCost": False,
                "linkStyle": "plain",
                "linkWidth": 1,
                "loopFlow": False,
                "transmissionCapacities": "enabled",
                "usePhaseShifter": False,
                "filterSynthesis": "hourly, daily, weekly, monthly, annual",
                "filterYearByYear": "hourly, daily, weekly, monthly, annual",
            },
            "es / fr": {
                "area1": "es",
                "area2": "fr",
                "assetType": "ac",
                "colorb": 100,
                "colorg": 150,
                "colorr": 200,
                "displayComments": True,
                "comments": "",
                "hurdlesCost": True,
                "linkStyle": "plain",
                "linkWidth": 1,
                "loopFlow": False,
                "transmissionCapacities": "enabled",
                "usePhaseShifter": True,
                "filterSynthesis": "monthly",
                "filterYearByYear": "weekly",
            },
            "fr / it": {
                "area1": "fr",
                "area2": "it",
                "assetType": "dc",
                "colorb": 112,
                "colorg": 112,
                "colorr": 112,
                "displayComments": True,
                "comments": "",
                "hurdlesCost": True,
                "linkStyle": "plain",
                "linkWidth": 1,
                "loopFlow": False,
                "transmissionCapacities": "enabled",
                "usePhaseShifter": False,
                "filterSynthesis": "",
                "filterYearByYear": "hourly",
            },
        }

        res = client.put(f"/v1/studies/{internal_study_id}/table-mode/links", json=json_input)
        assert res.status_code == 200, res.json()

        actual = res.json()
        expected_partial = copy.deepcopy(expected_links)
        del expected_partial["de / it"]
        assert actual == expected_partial

        res = client.get(f"/v1/studies/{internal_study_id}/table-mode/links")
        assert res.status_code == 200, res.json()
        assert res.json() == expected_links

        # GET request to make sure that the GET /links works
        res = client.get(f"/v1/studies/{internal_study_id}/links")
        assert res.status_code == 200, res.json()

        # Table Mode - Thermal Clusters
        # =============================

        # Get the schema of the thermals table
        res = client.get(
            "/v1/table-schema/thermals",
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

        _solar_values = {"group": "Other 2", "nominalCapacity": 500000, "unitCount": 17}
        _wind_on_values = {"group": "Nuclear", "nominalCapacity": 314159, "unitCount": 15, "co2": 123}
        if study_version >= 860:
            _solar_values["so2"] = 8.25
        if study_version >= 870:
            _solar_values.update({"costGeneration": "useCostTimeseries", "efficiency": 87, "variableOMCost": 12.5})

        res = client.put(
            f"/v1/studies/{internal_study_id}/table-mode/thermals",
            json={
                "de / 01_solar": _solar_values,
                "de / 02_wind_on": _wind_on_values,
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
                "group": "other 2",
                "lawForced": "uniform",
                "lawPlanned": "uniform",
                "marginalCost": 10,
                "marketBidCost": 10,
                "minDownTime": 1,
                "minStablePower": 0,
                "minUpTime": 1,
                "mustRun": False,
                "nominalCapacity": 500000,
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
                "group": "nuclear",
                "lawForced": "uniform",
                "lawPlanned": "uniform",
                "marginalCost": 20,
                "marketBidCost": 20,
                "minDownTime": 1,
                "minStablePower": 0,
                "minUpTime": 1,
                "mustRun": False,
                "nominalCapacity": 314159,
                "spinning": 0,
                "spreadCost": 0,
                "startupCost": 0,
                "unitCount": 15,
                "variableOMCost": None,
                "volatilityForced": 0,
                "volatilityPlanned": 0,
            },
        }

        if study_version >= 860:
            _values = dict.fromkeys(POLLUTANTS_860, 0)
            expected_thermals["de / 02_wind_on"].update(_values)
            expected_thermals["de / 01_solar"].update(_values, **{"so2": 8.25})
        else:
            _values = dict.fromkeys(POLLUTANTS_860)
            expected_thermals["de / 02_wind_on"].update(_values)
            expected_thermals["de / 01_solar"].update(_values)

        if study_version >= 870:
            _values = {"costGeneration": "SetManually", "efficiency": 100, "variableOMCost": 0}
            expected_thermals["de / 02_wind_on"].update(_values)
            _values = {"costGeneration": "useCostTimeseries", "efficiency": 87, "variableOMCost": 12.5}
            expected_thermals["de / 01_solar"].update(_values)

        assert res.json()["de / 01_solar"] == expected_thermals["de / 01_solar"]
        assert res.json()["de / 02_wind_on"] == expected_thermals["de / 02_wind_on"]

        res = client.get(
            f"/v1/studies/{internal_study_id}/table-mode/thermals",
            params={"columns": ",".join(["group", "unitCount", "nominalCapacity", "so2"])},
        )
        assert res.status_code == 200, res.json()
        expected: t.Dict[str, t.Dict[str, t.Any]]
        expected = {
            "de / 01_solar": {"group": "other 2", "nominalCapacity": 500000, "unitCount": 17},
            "de / 02_wind_on": {"group": "nuclear", "nominalCapacity": 314159, "unitCount": 15},
            "de / 03_wind_off": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "de / 04_res": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "de / 05_nuclear": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "de / 06_coal": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "de / 07_gas": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "de / 08_non-res": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "de / 09_hydro_pump": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "es / 01_solar": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "es / 02_wind_on": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "es / 03_wind_off": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "es / 04_res": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "es / 05_nuclear": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "es / 06_coal": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "es / 07_gas": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "es / 08_non-res": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "es / 09_hydro_pump": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "fr / 01_solar": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "fr / 02_wind_on": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "fr / 03_wind_off": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "fr / 04_res": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "fr / 05_nuclear": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "fr / 06_coal": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "fr / 07_gas": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "fr / 08_non-res": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "fr / 09_hydro_pump": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "it / 01_solar": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "it / 02_wind_on": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "it / 03_wind_off": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "it / 04_res": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "it / 05_nuclear": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "it / 06_coal": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "it / 07_gas": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "it / 08_non-res": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
            "it / 09_hydro_pump": {"group": "other 1", "nominalCapacity": 1000000, "unitCount": 1},
        }
        if study_version >= 860:
            for key in expected:
                expected[key]["so2"] = 0
            expected["de / 01_solar"]["so2"] = 8.25

        actual = res.json()
        assert actual == expected

        # Table Mode - Renewable Clusters
        # ===============================

        # only concerns studies after v8.1
        if study_version >= 810:
            # Parameter 'renewable-generation-modelling' must be set to 'clusters' instead of 'aggregated'.
            # The `enr_modelling` value must be set to "clusters" instead of "aggregated"
            args = {
                "target": "settings/generaldata/other preferences",
                "data": {"renewable-generation-modelling": "clusters"},
            }
            res = client.post(
                f"/v1/studies/{internal_study_id}/commands",
                json=[{"action": "update_config", "args": args}],
            )
            assert res.status_code == 200, res.json()

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
                        f"/v1/studies/{internal_study_id}/areas/{area_id}/clusters/renewable",
                        json=generator,
                    )
                    res.raise_for_status()

            # Get the schema of the renewables table
            res = client.get(
                "/v1/table-schema/renewables",
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
                f"/v1/studies/{internal_study_id}/table-mode/renewables",
                json={
                    "fr / Dieppe": {"enabled": False},
                    "fr / La Rochelle": {"enabled": True, "nominalCapacity": 3.1, "unitCount": 2},
                    "it / Pouilles": {"group": "wind onshore"},
                },
            )
            assert res.status_code == 200, res.json()

            res = client.get(
                f"/v1/studies/{internal_study_id}/table-mode/renewables",
                params={"columns": ",".join(["group", "enabled", "unitCount", "nominalCapacity"])},
            )
            assert res.status_code == 200, res.json()
            expected = {
                "fr / Dieppe": {"enabled": False, "group": "wind offshore", "nominalCapacity": 8, "unitCount": 62},
                "fr / La Rochelle": {"enabled": True, "group": "solar pv", "nominalCapacity": 3.1, "unitCount": 2},
                "fr / Oleron": {"enabled": True, "group": "wind offshore", "nominalCapacity": 15, "unitCount": 70},
                "it / Pouilles": {"enabled": False, "group": "wind onshore", "nominalCapacity": 11, "unitCount": 40},
                "it / Sardaigne": {"enabled": True, "group": "wind offshore", "nominalCapacity": 12, "unitCount": 86},
                "it / Sicile": {"enabled": True, "group": "solar pv", "nominalCapacity": 1.8, "unitCount": 1},
            }
            actual = res.json()
            assert actual == expected

        # Table Mode - Short Term Storage
        # ===============================

        # only concerns studies after v8.6
        if study_version >= 860:
            # Get the schema of the short-term storages table
            res = client.get(
                "/v1/table-schema/st-storages",
            )
            assert res.status_code == 200, res.json()
            actual = res.json()
            assert set(actual["properties"]) == {
                # read-only fields
                "id",
                "name",
                # Short-term storage fields
                "enabled",  # since v8.8
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
                        f"/v1/studies/{internal_study_id}/areas/{area_id}/storages",
                        json=storage,
                    )
                    res.raise_for_status()

            # Update some generators using the table mode
            _fr_siemes_values = {"injectionNominalCapacity": 1550, "withdrawalNominalCapacity": 1550}
            _fr_tesla_values = {"efficiency": 0.75, "initialLevel": 0.89, "initialLevelOptim": False}
            _it_storage3_values = {"group": "Pondage"}
            if study_version >= 880:
                _it_storage3_values["enabled"] = False

            res = client.put(
                f"/v1/studies/{internal_study_id}/table-mode/st-storages",
                json={
                    "fr / siemens": _fr_siemes_values,
                    "fr / tesla": _fr_tesla_values,
                    "it / storage3": _it_storage3_values,
                },
            )
            assert res.status_code == 200, res.json()
            actual = res.json()
            expected = {
                "fr / siemens": {
                    # "id": "siemens",
                    # "name": "Siemens",
                    "efficiency": 1,
                    "enabled": None,
                    "group": "battery",
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
                    "enabled": None,
                    "group": "battery",
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
                    "enabled": None,
                    "group": "pondage",
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
                    "enabled": None,
                    "group": "psp_open",
                    "initialLevel": 0.5,
                    "initialLevelOptim": True,
                    "injectionNominalCapacity": 567,
                    "reservoirCapacity": 500,
                    "withdrawalNominalCapacity": 456,
                },
            }

            if study_version >= 880:
                for key in expected:
                    expected[key]["enabled"] = True
                expected["it / storage3"]["enabled"] = False

            assert actual == expected

            res = client.get(
                f"/v1/studies/{internal_study_id}/table-mode/st-storages",
                params={
                    "columns": ",".join(
                        [
                            "group",
                            "injectionNominalCapacity",
                            "withdrawalNominalCapacity",
                            "reservoirCapacity",
                            "unknowColumn",  # should be ignored
                        ]
                    ),
                },
            )
            assert res.status_code == 200, res.json()
            expected = {
                "fr / siemens": {
                    "group": "battery",
                    "injectionNominalCapacity": 1550,
                    "reservoirCapacity": 1500,
                    "withdrawalNominalCapacity": 1550,
                },
                "fr / tesla": {
                    "group": "battery",
                    "injectionNominalCapacity": 1200,
                    "reservoirCapacity": 1200,
                    "withdrawalNominalCapacity": 1200,
                },
                "it / storage3": {
                    "group": "pondage",
                    "injectionNominalCapacity": 1234,
                    "reservoirCapacity": 1357,
                    "withdrawalNominalCapacity": 1020,
                },
                "it / storage4": {
                    "group": "psp_open",
                    "injectionNominalCapacity": 567,
                    "reservoirCapacity": 500,
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
            f"/v1/studies/{internal_study_id}/areas/{fr_id}/clusters/thermal",
            json={
                "name": "Cluster 1",
                "group": "nuclear",
            },
        )
        assert res.status_code == 200, res.json()
        cluster_id = res.json()["id"]
        assert cluster_id == "Cluster 1"

        # Create Binding Constraints
        res = client.post(
            f"/v1/studies/{internal_study_id}/bindingconstraints",
            json={
                "name": "Binding Constraint 1",
                "enabled": True,
                "time_step": "hourly",
                "operator": "less",
            },
        )
        assert res.status_code == 200, res.json()

        res = client.post(
            f"/v1/studies/{internal_study_id}/bindingconstraints",
            json={
                "name": "Binding Constraint 2",
                "enabled": False,
                "time_step": "daily",
                "operator": "greater",
                "comments": "This is a binding constraint",
                "filter_synthesis": "hourly, daily, weekly",
            },
        )
        assert res.status_code == 200, res.json()

        # Get the schema of the binding constraints table
        res = client.get(
            "/v1/table-schema/binding-constraints",
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        assert set(actual["properties"]) == {
            # read-only fields
            "id",
            "name",
            # Binding Constraints fields
            "group",  # since v8.7
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
        _bc1_values = {"comments": "Hello World!", "enabled": True}
        _bc2_values = {"filterSynthesis": "hourly", "filterYearByYear": "hourly", "operator": "both"}
        if study_version >= 870:
            _bc2_values["group"] = "My BC Group"

        res = client.put(
            f"/v1/studies/{internal_study_id}/table-mode/binding-constraints",
            json={
                "binding constraint 1": _bc1_values,
                "binding constraint 2": _bc2_values,
            },
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        expected_binding = {
            "binding constraint 1": {
                "comments": "Hello World!",
                "enabled": True,
                "operator": "less",
                "timeStep": "hourly",
            },
            "binding constraint 2": {
                "comments": "This is a binding constraint",
                "enabled": False,
                "operator": "both",
                "timeStep": "daily",
            },
        }
        if study_version >= 830:
            expected_binding["binding constraint 1"]["filterSynthesis"] = ""
            expected_binding["binding constraint 1"]["filterYearByYear"] = ""
            expected_binding["binding constraint 2"]["filterSynthesis"] = "hourly"
            expected_binding["binding constraint 2"]["filterYearByYear"] = "hourly"

        if study_version >= 870:
            expected_binding["binding constraint 1"]["group"] = "default"
            expected_binding["binding constraint 2"]["group"] = "my bc group"

        assert actual == expected_binding

        res = client.get(
            f"/v1/studies/{internal_study_id}/table-mode/binding-constraints",
            params={"columns": ""},
        )
        assert res.status_code == 200, res.json()
        expected = expected_binding
        actual = res.json()
        assert actual == expected


def test_table_type_aliases(client: TestClient, user_access_token: str) -> None:
    """
    Ensure that we can use the old table type aliases to get the schema of the tables.
    """
    client.headers = {"Authorization": f"Bearer {user_access_token}"}
    # do not use `pytest.mark.parametrize`, because it is too slow
    for table_type in ["area", "link", "cluster", "renewable", "binding constraint"]:
        res = client.get(f"/v1/table-schema/{table_type}")
        assert res.status_code == 200, f"Failed to get schema for {table_type}: {res.json()}"
