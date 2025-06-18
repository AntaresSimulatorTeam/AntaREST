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
from starlette.testclient import TestClient

from antarest.study.business.general_management import Mode
from antarest.study.business.optimization_management import (
    SimplexOptimizationRange,
    TransmissionCapacities,
    UnfeasibleProblemBehavior,
)


def test_study_settings(client: TestClient, admin_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    created = client.post("/v1/studies", params={"name": "foo", "version": 870})
    study_id = created.json()

    # Optimization form

    res_optimization_config = client.get(f"/v1/studies/{study_id}/config/optimization/form")
    res_optimization_config_json = res_optimization_config.json()
    assert res_optimization_config_json == {
        "bindingConstraints": True,
        "hurdleCosts": True,
        "transmissionCapacities": TransmissionCapacities.LOCAL_VALUES.value,
        "thermalClustersMinStablePower": True,
        "thermalClustersMinUdTime": True,
        "dayAheadReserve": True,
        "primaryReserve": True,
        "strategicReserve": True,
        "spinningReserve": True,
        "exportMps": False,
        "unfeasibleProblemBehavior": UnfeasibleProblemBehavior.ERROR_VERBOSE.value,
        "simplexOptimizationRange": SimplexOptimizationRange.WEEK.value,
    }

    res = client.put(
        f"/v1/studies/{study_id}/config/optimization/form",
        json={
            "strategicReserve": False,
            "unfeasibleProblemBehavior": UnfeasibleProblemBehavior.WARNING_VERBOSE.value,
            "simplexOptimizationRange": SimplexOptimizationRange.DAY.value,
        },
    )
    res.raise_for_status()
    res_optimization_config = client.get(f"/v1/studies/{study_id}/config/optimization/form")
    res_optimization_config_json = res_optimization_config.json()
    assert res_optimization_config_json == {
        "bindingConstraints": True,
        "hurdleCosts": True,
        "transmissionCapacities": TransmissionCapacities.LOCAL_VALUES.value,
        "thermalClustersMinStablePower": True,
        "thermalClustersMinUdTime": True,
        "dayAheadReserve": True,
        "primaryReserve": True,
        "strategicReserve": False,
        "spinningReserve": True,
        "exportMps": False,
        "unfeasibleProblemBehavior": UnfeasibleProblemBehavior.WARNING_VERBOSE.value,
        "simplexOptimizationRange": SimplexOptimizationRange.DAY.value,
    }

    # Adequacy patch form

    res_adequacy_patch_config = client.get(f"/v1/studies/{study_id}/config/adequacypatch/form")
    res_adequacy_patch_config_json = res_adequacy_patch_config.json()
    assert res_adequacy_patch_config_json == {
        "enableAdequacyPatch": False,
        "ntcFromPhysicalAreasOutToPhysicalAreasInAdequacyPatch": True,
        "ntcBetweenPhysicalAreasOutAdequacyPatch": True,
        "checkCsrCostFunction": False,
        "includeHurdleCostCsr": False,
        "priceTakingOrder": "DENS",
        "thresholdInitiateCurtailmentSharingRule": 1.0,
        "thresholdDisplayLocalMatchingRuleViolations": 0.0,
        "thresholdCsrVariableBoundsRelaxation": 7,
    }

    client.put(
        f"/v1/studies/{study_id}/config/adequacypatch/form",
        json={
            "ntcBetweenPhysicalAreasOutAdequacyPatch": False,
            "priceTakingOrder": "Load",
            "thresholdDisplayLocalMatchingRuleViolations": 1.1,
        },
    )
    res_adequacy_patch_config = client.get(f"/v1/studies/{study_id}/config/adequacypatch/form")
    res_adequacy_patch_config_json = res_adequacy_patch_config.json()
    assert res_adequacy_patch_config_json == {
        "enableAdequacyPatch": False,
        "ntcFromPhysicalAreasOutToPhysicalAreasInAdequacyPatch": True,
        "ntcBetweenPhysicalAreasOutAdequacyPatch": False,
        "checkCsrCostFunction": False,
        "includeHurdleCostCsr": False,
        "priceTakingOrder": "Load",
        "thresholdInitiateCurtailmentSharingRule": 1.0,
        "thresholdDisplayLocalMatchingRuleViolations": 1.1,
        "thresholdCsrVariableBoundsRelaxation": 7,
    }

    # asserts csr field is an int
    res = client.put(
        f"/v1/studies/{study_id}/config/adequacypatch/form",
        json={"thresholdCsrVariableBoundsRelaxation": 0.8},
    )
    assert res.status_code == 422
    assert res.json()["exception"] == "RequestValidationError"
    assert res.json()["description"] == "Input should be a valid integer"

    # General form

    res_general_config = client.get(f"/v1/studies/{study_id}/config/general/form")
    res_general_config_json = res_general_config.json()
    assert res_general_config_json == {
        "mode": "Economy",
        "firstDay": 1,
        "lastDay": 365,
        "horizon": "",
        "firstMonth": "january",
        "firstWeekDay": "Monday",
        "firstJanuary": "Monday",
        "leapYear": False,
        "nbYears": 1,
        "buildingMode": "Automatic",
        "selectionMode": False,
        "yearByYear": False,
        "simulationSynthesis": True,
        "mcScenario": False,
        "geographicTrimming": False,
        "thematicTrimming": False,
    }

    client.put(
        f"/v1/studies/{study_id}/config/general/form",
        json={
            "mode": Mode.ADEQUACY.value,
            "firstDay": 2,
            "lastDay": 299,
            "leapYear": True,
        },
    )
    res_general_config = client.get(f"/v1/studies/{study_id}/config/general/form")
    res_general_config_json = res_general_config.json()
    assert res_general_config_json == {
        "mode": Mode.ADEQUACY.value,
        "firstDay": 2,
        "lastDay": 299,
        "horizon": "",
        "firstMonth": "january",
        "firstWeekDay": "Monday",
        "firstJanuary": "Monday",
        "leapYear": True,
        "nbYears": 1,
        "buildingMode": "Automatic",
        "selectionMode": False,
        "yearByYear": False,
        "simulationSynthesis": True,
        "mcScenario": False,
        "geographicTrimming": False,
        "thematicTrimming": False,
    }

    # Thematic trimming form

    res = client.get(f"/v1/studies/{study_id}/config/thematictrimming/form")
    obj = res.json()
    assert obj == {
        "avlDtg": True,
        "balance": True,
        "batteryInjection": True,
        "batteryLevel": True,
        "batteryWithdrawal": True,
        "co2Emis": True,
        "coal": True,
        "congFeeAbs": True,
        "congFeeAlg": True,
        "congProbMinus": True,
        "congProbPlus": True,
        "dens": True,
        "dtgByPlant": True,
        "dtgMrg": True,
        "flowLin": True,
        "flowQuad": True,
        "gas": True,
        "hCost": True,
        "hInfl": True,
        "hLev": True,
        "hOvfl": True,
        "hPump": True,
        "hRor": True,
        "hStor": True,
        "hVal": True,
        "hurdleCost": True,
        "lignite": True,
        "load": True,
        "lold": True,
        "lolp": True,
        "loopFlow": True,
        "margCost": True,
        "maxMrg": True,
        "miscDtg": True,
        "miscDtg2": True,
        "miscDtg3": True,
        "miscDtg4": True,
        "miscNdg": True,
        "mixFuel": True,
        "mrgPrice": True,
        "nodu": True,
        "noduByPlant": True,
        "npCost": True,
        "npCostByPlant": True,
        "nuclear": True,
        "oil": True,
        "opCost": True,
        "other1Injection": True,
        "other1Level": True,
        "other1Withdrawal": True,
        "other2Injection": True,
        "other2Level": True,
        "other2Withdrawal": True,
        "other3Injection": True,
        "other3Level": True,
        "other3Withdrawal": True,
        "other4Injection": True,
        "other4Level": True,
        "other4Withdrawal": True,
        "other5Injection": True,
        "other5Level": True,
        "other5Withdrawal": True,
        "ovCost": True,
        "pondageInjection": True,
        "pondageLevel": True,
        "pondageWithdrawal": True,
        "profitByPlant": True,
        "psp": True,
        "pspClosedInjection": True,
        "pspClosedLevel": True,
        "pspClosedWithdrawal": True,
        "pspOpenInjection": True,
        "pspOpenLevel": True,
        "pspOpenWithdrawal": True,
        "renw1": True,
        "renw2": True,
        "renw3": True,
        "renw4": True,
        "resGenerationByPlant": True,
        "rowBal": True,
        "solar": True,
        "solarConcrt": True,
        "solarPv": True,
        "solarRooft": True,
        "spilEnrg": True,
        "stsInjByPlant": True,
        "stsLvlByPlant": True,
        "stsWithdrawalByPlant": True,
        "ucapLin": True,
        "unspEnrg": True,
        "wind": True,
        "windOffshore": True,
        "windOnshore": True,
    }

    new_thematic_trimming = {
        "ovCost": False,
        "opCost": True,
        "mrgPrice": True,
        "co2Emis": True,
        "dtgByPlant": True,
        "balance": True,
        "rowBal": True,
        "psp": True,
        "miscNdg": True,
        "load": True,
        "hRor": True,
        "wind": True,
        "solar": True,
        "nuclear": True,
        "lignite": True,
        "coal": True,
        "gas": True,
        "oil": True,
        "mixFuel": True,
        "miscDtg": True,
        "hStor": True,
        "hPump": True,
        "hLev": True,
        "hInfl": True,
        "hOvfl": True,
        "hVal": False,
        "hCost": True,
        "unspEnrg": True,
        "spilEnrg": True,
        "lold": True,
        "lolp": True,
        "avlDtg": True,
        "dtgMrg": True,
        "maxMrg": True,
        "npCost": True,
        "npCostByPlant": True,
        "nodu": True,
        "noduByPlant": True,
        "flowLin": True,
        "ucapLin": True,
        "loopFlow": True,
        "flowQuad": True,
        "congFeeAlg": True,
        "congFeeAbs": True,
        "margCost": True,
        "congProbPlus": True,
        "congProbMinus": True,
        "hurdleCost": True,
        "resGenerationByPlant": True,
        "miscDtg2": True,
        "miscDtg3": True,
        "miscDtg4": True,
        "windOffshore": True,
        "windOnshore": True,
        "solarConcrt": True,
        "solarPv": True,
        "solarRooft": True,
        "renw1": True,
        "renw2": False,
        "renw3": True,
        "renw4": True,
        "dens": True,
        "profitByPlant": True,
        "stsInjByPlant": True,
        "stsWithdrawalByPlant": True,
        "stsLvlByPlant": True,
        "pspOpenInjection": True,
        "pspOpenWithdrawal": True,
        "pspOpenLevel": True,
        "pspClosedInjection": True,
        "pspClosedWithdrawal": True,
        "pspClosedLevel": True,
        "pondageInjection": True,
        "pondageWithdrawal": True,
        "pondageLevel": True,
        "batteryInjection": True,
        "batteryWithdrawal": True,
        "batteryLevel": True,
        "other1Injection": True,
        "other1Withdrawal": True,
        "other1Level": True,
        "other2Injection": True,
        "other2Withdrawal": True,
        "other2Level": True,
        "other3Injection": True,
        "other3Withdrawal": True,
        "other3Level": True,
        "other4Injection": True,
        "other4Withdrawal": True,
        "other4Level": True,
        "other5Injection": True,
        "other5Withdrawal": True,
        "other5Level": True,
    }

    res = client.put(f"/v1/studies/{study_id}/config/thematictrimming/form", json=new_thematic_trimming)
    res.raise_for_status()
    res = client.get(f"/v1/studies/{study_id}/config/thematictrimming/form")
    obj = res.json()
    assert obj == new_thematic_trimming

    # Time-series form

    res_ts_config = client.get(f"/v1/studies/{study_id}/timeseries/config")
    res_ts_config_json = res_ts_config.json()
    assert res_ts_config_json == {"thermal": {"number": 1}}
    client.put(f"/v1/studies/{study_id}/timeseries/config", json={"thermal": {"number": 2}})
    res_ts_config = client.get(f"/v1/studies/{study_id}/timeseries/config")
    res_ts_config_json = res_ts_config.json()
    assert res_ts_config_json == {"thermal": {"number": 2}}
