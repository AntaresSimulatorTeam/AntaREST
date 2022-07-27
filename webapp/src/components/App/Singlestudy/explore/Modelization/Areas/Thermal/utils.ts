import { FieldValues } from "react-hook-form";
import { Cluster } from "../../../../../../../common/types";
import { getStudyData } from "../../../../../../../services/api/study";

type GenTsType =
  | "use global parameter"
  | "force no generation"
  | "force generation";

type LawType = "geometric" | "uniform";

export interface ThermalType extends FieldValues {
  name: string;
  group: string;
  enabled?: boolean; // Default: true
  unitcount?: number; // Default: 0
  nominalcapacity?: number; // Default: 0
  "gen-ts"?: GenTsType; // Default: use global parameter
  "min-stable-power"?: number; // Default: 0
  "min-up-time"?: number; // Default: 1
  "min-down-time"?: number; // Default: 1
  "must-run"?: boolean; // Default: false
  spinning?: number; // Default: 0
  co2?: number; // Default: 0
  "volatility.forced"?: number; // Default: 0
  "volatility.planned"?: number; // Default: 0
  "law.forced"?: LawType; // Default: uniform
  "law.planned"?: LawType; // Default: uniform
  "marginal-cost"?: number; // Default: 0
  "spread-cost"?: number; // Default: 0
  "fixed-cost"?: number; // Default: 0
  "startup-cost"?: number; // Default: 0
  "market-bid-cost"?: number; // Default: 0 */
}

export const noDataValues: Partial<ThermalType> = {
  name: "",
  group: "",
  enabled: true,
  unitcount: 0,
  nominalcapacity: 0,
  "gen-ts": "use global parameter",
  "min-stable-power": 0,
  "min-up-time": 1,
  "min-down-time": 1,
  "must-run": false,
  spinning: 0,
  co2: 0,
  "volatility.forced": 0,
  "volatility.planned": 0,
  "law.forced": "uniform",
  "law.planned": "uniform",
  "marginal-cost": 0,
  "spread-cost": 0,
  "fixed-cost": 0,
  "startup-cost": 0,
  "market-bid-cost": 0,
};

export const genTsOptions = [
  "use global parameter",
  "force no generation",
  "force generation",
].map((item) => ({ label: item, value: item }));

export const lawOptions = ["uniform", "geometric"].map((item) => ({
  label: item,
  value: item,
}));

export const fixedGroupList = [
  "Gas",
  "Hard Coal",
  "Lignite",
  "Mixed fuel",
  "Nuclear",
  "Oil",
  "Other",
  "Other 2",
  "Other 3",
  "Other 4",
];

export type ThermalPath = Record<keyof ThermalType, string>;

export async function getDefaultValues(
  studyId: string,
  area: string,
  cluster: Cluster["id"]
): Promise<ThermalType> {
  const pathPrefix = `input/thermal/clusters/${area}/list/${cluster}`;
  const data: ThermalType = await getStudyData(studyId, pathPrefix, 3);
  Object.keys(noDataValues).forEach((item) => {
    data[item] = data[item] !== undefined ? data[item] : noDataValues[item];
  });
  return data;
}

export default {};
