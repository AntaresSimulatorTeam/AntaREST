import { FieldValues } from "react-hook-form";
import { Cluster } from "../../../../../../../../common/types";
import { getStudyData } from "../../../../../../../../services/api/study";

type GenTsType =
  | "use global parameter"
  | "force no generation"
  | "force generation";

type LawType = "geometric" | "uniform";

export interface ThermalType {
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

export interface ThermalFields extends FieldValues {
  name: string;
  group: string;
  enabled?: boolean; // Default: true
  unitcount?: number; // Default: 0
  nominalCapacity?: number; // Default: 0
  genTs?: GenTsType; // Default: use global parameter
  minStablePower?: number; // Default: 0
  minUpTime?: number; // Default: 1
  minDownTime?: number; // Default: 1
  mustRun?: boolean; // Default: false
  spinning?: number; // Default: 0
  co2?: number; // Default: 0
  volatilityForced?: number; // Default: 0
  volatilityPlanned?: number; // Default: 0
  lawForced?: LawType; // Default: uniform
  lawPlanned?: LawType; // Default: uniform
  marginalCost?: number; // Default: 0
  spreadCost?: number; // Default: 0
  fixedCost?: number; // Default: 0
  startupCost?: number; // Default: 0
  marketBidCost?: number; // Default: 0
}

export type ThermalPath = Record<keyof ThermalFields, string>;

export async function getDefaultValues(
  studyId: string,
  area: string,
  cluster: Cluster["id"]
): Promise<ThermalFields> {
  const pathPrefix = `input/thermal/clusters/${area}/list/${cluster}`;
  const data: ThermalType = await getStudyData(studyId, pathPrefix, 3);
  return {
    name: data.name,
    group: data.group,
    enabled: data.enabled,
    unitcount: data.unitcount,
    nominalCapacity: data.nominalcapacity,
    genTs: data["gen-ts"],
    minStablePower: data["min-stable-power"],
    minUpTime: data["min-up-time"],
    minDownTime: data["min-down-time"],
    mustRun: data["must-run"],
    spinning: data.spinning,
    co2: data.co2,
    volatilityForced: data["volatility.forced"],
    volatilityPlanned: data["volatility.planned"],
    lawForced: data["law.forced"],
    lawPlanned: data["law.planned"],
    marginalCost: data["marginal-cost"],
    spreadCost: data["spread-cost"],
    fixedCost: data["fixed-cost"],
    startupCost: data["startup-cost"],
    marketBidCost: data["market-bid-cost"],
  };
}

export function getThermalPath(area: string, cluster: string): ThermalPath {
  const pathPrefix = `input/thermal/clusters/${area}/list/${cluster}`;
  return {
    name: `${pathPrefix}/name`,
    group: `${pathPrefix}/group`,
    enabled: `${pathPrefix}/enabled`,
    unitcount: `${pathPrefix}/unitcount`,
    nominalCapacity: `${pathPrefix}/nominalcapacity`,
    genTs: `${pathPrefix}/gen-ts`,
    minStablePower: `${pathPrefix}/min-stable-power`,
    minUpTime: `${pathPrefix}/min-up-time`,
    minDownTime: `${pathPrefix}/min-down-time`,
    mustRun: `${pathPrefix}/must-run`,
    spinning: `${pathPrefix}/spinning`,
    co2: `${pathPrefix}/co2`,
    volatilityForced: `${pathPrefix}/volatility.forced`,
    volatilityPlanned: `${pathPrefix}/volatility.planned`,
    lawForced: `${pathPrefix}/law.forced`,
    lawPlanned: `${pathPrefix}/law.planned`,
    marginalCost: `${pathPrefix}/marginal-cost`,
    spreadCost: `${pathPrefix}/spread-cost`,
    fixedCost: `${pathPrefix}/fixed-cost`,
    startupCost: `${pathPrefix}/startup-cost`,
    marketBidCost: `${pathPrefix}/market-bid-cost`,
  };
}

export default {};
