import * as R from "ramda";
import { StudyMetadata } from "../../../../../../../../common/types";
import client from "../../../../../../../../services/api/client";

export interface ThematicTrimmingFormFields {
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
  // Study version >= 810
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
  // Study version >= 830
  dens?: boolean;
  profitByPlant?: boolean;
  // Study version >= 860
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
  // Study version >= 880
  stsCashflowByCluster?: boolean;
}

const keysMap: Record<keyof ThematicTrimmingFormFields, string> = {
  ovCost: "OV. COST",
  opCost: "OP. COST",
  mrgPrice: "MRG. PRICE",
  co2Emis: "CO2 EMIS.",
  dtgByPlant: "DTG BY PLANT",
  balance: "BALANCE",
  rowBal: "ROW BAL.",
  psp: "PSP",
  miscNdg: "MISC. NDG",
  load: "LOAD",
  hRor: "H. ROR",
  wind: "WIND",
  solar: "SOLAR",
  nuclear: "NUCLEAR",
  lignite: "LIGNITE",
  coal: "COAL",
  gas: "GAS",
  oil: "OIL",
  mixFuel: "MIX. FUEL",
  miscDtg: "MISC. DTG",
  hStor: "H. STOR",
  hPump: "H. PUMP",
  hLev: "H. LEV",
  hInfl: "H. INFL",
  hOvfl: "H. OVFL",
  hVal: "H. VAL",
  hCost: "H. COST",
  unspEnrg: "UNSP. ENRG",
  spilEnrg: "SPIL. ENRG",
  lold: "LOLD",
  lolp: "LOLP",
  avlDtg: "AVL DTG",
  dtgMrg: "DTG MRG",
  maxMrg: "MAX MRG",
  npCost: "NP COST",
  npCostByPlant: "NP COST BY PLANT",
  nodu: "NODU",
  noduByPlant: "NODU BY PLANT",
  flowLin: "FLOW LIN.",
  ucapLin: "UCAP LIN.",
  loopFlow: "LOOP FLOW",
  flowQuad: "FLOW QUAD.",
  congFeeAlg: "CONG. FEE (ALG.)",
  congFeeAbs: "CONG. FEE (ABS.)",
  margCost: "MARG. COST",
  congProbPlus: "CONG. PROB +",
  congProbMinus: "CONG. PROB -",
  hurdleCost: "HURDLE COST",
  // Study version >= 810
  resGenerationByPlant: "RES GENERATION BY PLANT",
  miscDtg2: "MISC. DTG 2",
  miscDtg3: "MISC. DTG 3",
  miscDtg4: "MISC. DTG 4",
  windOffshore: "WIND OFFSHORE",
  windOnshore: "WIND ONSHORE",
  solarConcrt: "SOLAR CONCRT.",
  solarPv: "SOLAR PV",
  solarRooft: "SOLAR ROOFT",
  renw1: "RENW. 1",
  renw2: "RENW. 2",
  renw3: "RENW. 3",
  renw4: "RENW. 4",
  // Study version >= 830
  dens: "DENS",
  profitByPlant: "PROFIT BY PLANT",
  // Study version >= 860
  stsInjByPlant: "STS INJ BY PLANT",
  stsWithdrawalByPlant: "STS WITHDRAWAL BY PLANT",
  stsLvlByPlant: "STS LVL BY PLANT",
  pspOpenInjection: "PSP OPEN INJECTION",
  pspOpenWithdrawal: "PSP OPEN WITHDRAWAL",
  pspOpenLevel: "PSP OPEN LEVEL",
  pspClosedInjection: "PSP CLOSED INJECTION",
  pspClosedWithdrawal: "PSP CLOSED WITHDRAWAL",
  pspClosedLevel: "PSP CLOSED LEVEL",
  pondageInjection: "PONDAGE INJECTION",
  pondageWithdrawal: "PONDAGE WITHDRAWAL",
  pondageLevel: "PONDAGE LEVEL",
  batteryInjection: "BATTERY INJECTION",
  batteryWithdrawal: "BATTERY WITHDRAWAL",
  batteryLevel: "BATTERY LEVEL",
  other1Injection: "OTHER1 INJECTION",
  other1Withdrawal: "OTHER1 WITHDRAWAL",
  other1Level: "OTHER1 LEVEL",
  other2Injection: "OTHER2 INJECTION",
  other2Withdrawal: "OTHER2 WITHDRAWAL",
  other2Level: "OTHER2 LEVEL",
  other3Injection: "OTHER3 INJECTION",
  other3Withdrawal: "OTHER3 WITHDRAWAL",
  other3Level: "OTHER3 LEVEL",
  other4Injection: "OTHER4 INJECTION",
  other4Withdrawal: "OTHER4 WITHDRAWAL",
  other4Level: "OTHER4 LEVEL",
  other5Injection: "OTHER5 INJECTION",
  other5Withdrawal: "OTHER5 WITHDRAWAL",
  other5Level: "OTHER5 LEVEL",
  // Study version >= 880
  stsCashflowByCluster: "STS CASHFLOW BY CLUSTER",
};

// Allow to support all study versions by using directly the server config
export function getFieldNames(
  fields: ThematicTrimmingFormFields,
): Array<[keyof ThematicTrimmingFormFields, string]> {
  return R.toPairs(R.pick(R.keys(fields), keysMap));
}

function makeRequestURL(studyId: StudyMetadata["id"]): string {
  return `/v1/studies/${studyId}/config/thematictrimming/form`;
}

export const getThematicTrimmingFormFields = async (
  studyId: StudyMetadata["id"],
): Promise<ThematicTrimmingFormFields> => {
  const res = await client.get(makeRequestURL(studyId));
  return res.data;
};

export const setThematicTrimmingConfig = async (
  studyId: StudyMetadata["id"],
  config: ThematicTrimmingFormFields,
): Promise<void> => {
  await client.put(makeRequestURL(studyId), config);
};
