import * as R from "ramda";
import { StudyMetadata } from "../../../../../../../../common/types";
import client from "../../../../../../../../services/api/client";

// noinspection SpellCheckingInspection
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
  stsCashflowByCluster?: boolean;
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
}

// noinspection SpellCheckingInspection
const keysMap: Record<keyof ThematicTrimmingFormFields, string> = {
  ovCost: "OV. COST",
  opCost: "OP. COST",
  mrgPrice: "MRG. PRICE",
  co2Emis: "CO2 EMIS.",
  dtgByPlant: "DTG by plant",
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
  npCostByPlant: "NP Cost by plant",
  nodu: "NODU",
  noduByPlant: "NODU by plant",
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
  resGenerationByPlant: "RES generation by plant",
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
  profitByPlant: "Profit by plant",
  // Study version >= 860
  stsInjByPlant: "STS inj by plant",
  stsWithdrawalByPlant: "STS withdrawal by plant",
  stsLvlByPlant: "STS lvl by plant",
  stsCashflowByCluster: "STS Cashflow By Cluster",
  pspOpenInjection: "PSP_open_injection",
  pspOpenWithdrawal: "PSP_open_withdrawal",
  pspOpenLevel: "PSP_open_level",
  pspClosedInjection: "PSP_closed_injection",
  pspClosedWithdrawal: "PSP_closed_withdrawal",
  pspClosedLevel: "PSP_closed_level",
  pondageInjection: "Pondage_injection",
  pondageWithdrawal: "Pondage_withdrawal",
  pondageLevel: "Pondage_level",
  batteryInjection: "Battery_injection",
  batteryWithdrawal: "Battery_withdrawal",
  batteryLevel: "Battery_level",
  other1Injection: "Other1_injection",
  other1Withdrawal: "Other1_withdrawal",
  other1Level: "Other1_level",
  other2Injection: "Other2_injection",
  other2Withdrawal: "Other2_withdrawal",
  other2Level: "Other2_level",
  other3Injection: "Other3_injection",
  other3Withdrawal: "Other3_withdrawal",
  other3Level: "Other3_level",
  other4Injection: "Other4_injection",
  other4Withdrawal: "Other4_withdrawal",
  other4Level: "Other4_level",
  other5Injection: "Other5_injection",
  other5Withdrawal: "Other5_withdrawal",
  other5Level: "Other5_level",
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
