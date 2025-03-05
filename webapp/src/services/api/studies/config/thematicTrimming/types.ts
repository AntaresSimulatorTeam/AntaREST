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

import type { StudyMetadata } from "../../../../../types/types";

export interface ThematicTrimmingConfig {
  ovCost: boolean;
  opCost: boolean;
  mrgPrice: boolean;
  co2Emis: boolean;
  dtgByPlant: boolean;
  balance: boolean;
  rowBal: boolean;
  psp: boolean;
  miscNdg: boolean;
  load: boolean;
  hRor: boolean;
  wind: boolean;
  solar: boolean;
  nuclear: boolean;
  lignite: boolean;
  coal: boolean;
  gas: boolean;
  oil: boolean;
  mixFuel: boolean;
  miscDtg: boolean;
  hStor: boolean;
  hPump: boolean;
  hLev: boolean;
  hInfl: boolean;
  hOvfl: boolean;
  hVal: boolean;
  hCost: boolean;
  unspEnrg: boolean;
  spilEnrg: boolean;
  lold: boolean;
  lolp: boolean;
  avlDtg: boolean;
  dtgMrg: boolean;
  maxMrg: boolean;
  npCost: boolean;
  npCostByPlant: boolean;
  nodu: boolean;
  noduByPlant: boolean;
  flowLin: boolean;
  ucapLin: boolean;
  loopFlow: boolean;
  flowQuad: boolean;
  congFeeAlg: boolean;
  congFeeAbs: boolean;
  margCost: boolean;
  congProbPlus: boolean;
  congProbMinus: boolean;
  hurdleCost: boolean;
  // Since v8.1
  resGenerationByPlant?: boolean;
  miscDtg2?: boolean;
  miscDtg3?: boolean;
  miscDtg4?: boolean;
  windOffshore?: boolean;
  windOnshore?: boolean;
  solarConcrt?: boolean;
  solarPv?: boolean;
  solarRooft?: boolean;
  renw1?: boolean;
  renw2?: boolean;
  renw3?: boolean;
  renw4?: boolean;
  // Since v8.3
  dens?: boolean;
  profitByPlant?: boolean;
  // Since v8.6
  stsInjByPlant?: boolean;
  stsWithdrawalByPlant?: boolean;
  stsLvlByPlant?: boolean;
  pspOpenInjection?: boolean;
  pspOpenWithdrawal?: boolean;
  pspOpenLevel?: boolean;
  pspClosedInjection?: boolean;
  pspClosedWithdrawal?: boolean;
  pspClosedLevel?: boolean;
  pondageInjection?: boolean;
  pondageWithdrawal?: boolean;
  pondageLevel?: boolean;
  batteryInjection?: boolean;
  batteryWithdrawal?: boolean;
  batteryLevel?: boolean;
  other1Injection?: boolean;
  other1Withdrawal?: boolean;
  other1Level?: boolean;
  other2Injection?: boolean;
  other2Withdrawal?: boolean;
  other2Level?: boolean;
  other3Injection?: boolean;
  other3Withdrawal?: boolean;
  other3Level?: boolean;
  other4Injection?: boolean;
  other4Withdrawal?: boolean;
  other4Level?: boolean;
  other5Injection?: boolean;
  other5Withdrawal?: boolean;
  other5Level?: boolean;
  // Since v8.8
  stsCashflowByCluster?: boolean;
}

export interface GetThematicTrimmingConfigParams {
  studyId: StudyMetadata["id"];
}

export interface SetThematicTrimmingConfigParams {
  studyId: StudyMetadata["id"];
  config: ThematicTrimmingConfig;
}
