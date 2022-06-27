import { camelCase } from "lodash";
import * as R from "ramda";
import * as RA from "ramda-adjunct";
import {
  StudyMetadata,
  ThematicTrimmingConfigDTO,
} from "../../../../../../../../common/types";

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
  congProdPlus: boolean;
  congProdMinus: boolean;
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
}

const keysMap = {
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
  congProdPlus: "CONG. PROD +",
  congProdMinus: "CONG. PROD -",
  hurdleCost: "HURDLE COST",
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
};

export function formatThematicTrimmingConfigDTO(
  configDTO: ThematicTrimmingConfigDTO
): ThematicTrimmingConfig {
  return Object.entries(configDTO).reduce((acc, [key, value]) => {
    const newKey = R.cond([
      [R.equals("CONG. PROD +"), R.always("congProdPlus")],
      [R.equals("CONG. PROD -"), R.always("congProdMinus")],
      [R.T, camelCase],
    ])(key) as keyof ThematicTrimmingConfig;

    acc[newKey] = value;
    return acc;
  }, {} as ThematicTrimmingConfig);
}

export function thematicTrimmingConfigToDTO(
  config: ThematicTrimmingConfig
): ThematicTrimmingConfigDTO {
  return RA.renameKeys(keysMap, config) as ThematicTrimmingConfigDTO;
}

export function getColumns(
  studyVersion: StudyMetadata["version"]
): Array<Array<[string, keyof ThematicTrimmingConfig]>> {
  const version = Number(studyVersion);

  return [
    [
      ["OV. Cost", "ovCost"],
      ["CO2 Emis.", "co2Emis"],
      ["Balance", "balance"],
      ["MISC. NDG", "miscNdg"],
      ["Wind", "wind"],
      ["Lignite", "lignite"],
    ],
    [
      ["OP. Cost", "opCost"],
      ["DTG by plant", "dtgByPlant"],
      ["Row bal.", "rowBal"],
      ["Load", "load"],
      ["Solar", "solar"],
    ],
    [
      ["MRG. Price", "mrgPrice"],
      version >= 810 && ["RES generation by plant", "resGenerationByPlant"],
      ["PSP", "psp"],
      ["H. ROR", "hRor"],
      ["Nuclear", "nuclear"],
    ].filter(Boolean) as Array<[string, keyof ThematicTrimmingConfig]>,
  ];
}

export function getFieldNames(
  studyVersion: StudyMetadata["version"]
): Array<keyof ThematicTrimmingConfig> {
  return getColumns(studyVersion).flatMap((column) => {
    return column.map(([, fieldName]) => fieldName);
  });
}
