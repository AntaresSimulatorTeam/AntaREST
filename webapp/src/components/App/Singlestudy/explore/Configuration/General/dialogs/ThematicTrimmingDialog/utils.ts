/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import * as R from "ramda";
import type { ThematicTrimmingConfig } from "../../../../../../../../services/api/studies/config/thematicTrimming/types";
import type { O } from "ts-toolbelt";

export const THEMATIC_TRIMMING_GROUPS = [
  "general",
  "generationHydro",
  "generationRenewables",
  "generationStStorages",
  "generationThermals",
  "links",
] as const;

export type ThematicTrimmingGroup = (typeof THEMATIC_TRIMMING_GROUPS)[number];

const fieldLabelsByGroup: Record<
  ThematicTrimmingGroup,
  Partial<O.Replace<ThematicTrimmingConfig, boolean, string>>
> = {
  general: {
    balance: "BALANCE",
    dens: "DENS",
    load: "LOAD",
    lold: "LOLD",
    lolp: "LOLP",
    miscNdg: "MISC. NDG",
    mrgPrice: "MRG. PRICE",
    opCost: "OP. COST",
    ovCost: "OV. COST",
    rowBal: "ROW BAL.",
    spilEnrg: "SPIL. ENRG",
    unspEnrg: "UNSP. ENRG",
  },
  generationHydro: {
    hCost: "H. COST",
    hInfl: "H. INFL",
    hLev: "H. LEV",
    hOvfl: "H. OVFL",
    hPump: "H. PUMP",
    hRor: "H. ROR",
    hStor: "H. STOR",
    hVal: "H. VAL",
    psp: "PSP",
  },
  generationRenewables: {
    renw1: "RENW. 1",
    renw2: "RENW. 2",
    renw3: "RENW. 3",
    renw4: "RENW. 4",
    resGenerationByPlant: "RES GENERATION BY PLANT",
    solar: "SOLAR",
    solarConcrt: "SOLAR CONCRT.",
    solarPv: "SOLAR PV",
    solarRooft: "SOLAR ROOFT",
    wind: "WIND",
    windOffshore: "WIND OFFSHORE",
    windOnshore: "WIND ONSHORE",
  },
  generationStStorages: {
    batteryInjection: "BATTERY INJECTION",
    batteryLevel: "BATTERY LEVEL",
    batteryWithdrawal: "BATTERY WITHDRAWAL",
    other1Injection: "OTHER1 INJECTION",
    other1Level: "OTHER1 LEVEL",
    other1Withdrawal: "OTHER1 WITHDRAWAL",
    other2Injection: "OTHER2 INJECTION",
    other2Level: "OTHER2 LEVEL",
    other2Withdrawal: "OTHER2 WITHDRAWAL",
    other3Injection: "OTHER3 INJECTION",
    other3Level: "OTHER3 LEVEL",
    other3Withdrawal: "OTHER3 WITHDRAWAL",
    other4Injection: "OTHER4 INJECTION",
    other4Level: "OTHER4 LEVEL",
    other4Withdrawal: "OTHER4 WITHDRAWAL",
    other5Injection: "OTHER5 INJECTION",
    other5Level: "OTHER5 LEVEL",
    other5Withdrawal: "OTHER5 WITHDRAWAL",
    pondageInjection: "PONDAGE INJECTION",
    pondageLevel: "PONDAGE LEVEL",
    pondageWithdrawal: "PONDAGE WITHDRAWAL",
    pspClosedInjection: "PSP CLOSED INJECTION",
    pspClosedLevel: "PSP CLOSED LEVEL",
    pspClosedWithdrawal: "PSP CLOSED WITHDRAWAL",
    pspOpenInjection: "PSP OPEN INJECTION",
    pspOpenLevel: "PSP OPEN LEVEL",
    pspOpenWithdrawal: "PSP OPEN WITHDRAWAL",
    stsCashflowByCluster: "STS CASHFLOW BY CLUSTER",
    stsInjByPlant: "STS INJ BY PLANT",
    stsLvlByPlant: "STS LVL BY PLANT",
    stsWithdrawalByPlant: "STS WITHDRAWAL BY PLANT",
    stsByGroup: "STS BY GROUP",
  },
  generationThermals: {
    avlDtg: "AVL DTG",
    co2Emis: "CO2 EMIS.",
    coal: "COAL",
    dtgByPlant: "DTG BY PLANT",
    dtgMrg: "DTG MRG",
    gas: "GAS",
    lignite: "LIGNITE",
    maxMrg: "MAX MRG",
    miscDtg: "MISC. DTG",
    miscDtg2: "MISC. DTG 2",
    miscDtg3: "MISC. DTG 3",
    miscDtg4: "MISC. DTG 4",
    mixFuel: "MIX. FUEL",
    nodu: "NODU",
    noduByPlant: "NODU BY PLANT",
    npCost: "NP COST",
    npCostByPlant: "NP COST BY PLANT",
    nuclear: "NUCLEAR",
    oil: "OIL",
    profitByPlant: "PROFIT BY PLANT",
  },
  links: {
    congFeeAbs: "CONG. FEE (ABS.)",
    congFeeAlg: "CONG. FEE (ALG.)",
    congProbMinus: "CONG. PROB -",
    congProbPlus: "CONG. PROB +",
    flowLin: "FLOW LIN.",
    flowQuad: "FLOW QUAD.",
    hurdleCost: "HURDLE COST",
    loopFlow: "LOOP FLOW",
    margCost: "MARG. COST",
    ucapLin: "UCAP LIN.",
  },
};

/**
 * Get thematic trimming field names and labels from specified config and group.
 *
 * Allows to support all study versions by only returning the fields that are present
 * in the server response.
 *
 * @param config - Thematic trimming config.
 * @param group - Thematic trimming form group.
 * @returns Field names and labels in tuple format.
 */
export function getFieldLabelsForGroup(
  config: ThematicTrimmingConfig,
  group: ThematicTrimmingGroup,
) {
  const labelsByName = R.pick(R.keys(config), fieldLabelsByGroup[group]);
  const pairs = R.toPairs(labelsByName).filter(Boolean);

  return R.sortBy(R.propOr("", "1"), pairs);
}
