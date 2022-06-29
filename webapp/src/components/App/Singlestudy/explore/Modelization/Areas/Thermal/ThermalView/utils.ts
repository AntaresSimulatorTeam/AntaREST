import { FieldValues } from "react-hook-form";

type GenTsType =
  | "use global parameter"
  | "force no generation"
  | "force generation";

type LawType = "geometric" | "uniform";

export interface ThermalFields extends FieldValues {
  name: string;
  group: string;
  enabled?: boolean; // Default: true
  unitcount?: number; // Default: 0
  nominalcapacity?: number; // Default: 0
  genTs?: GenTsType; // Default: use global parameter
  minStablePower?: number; // Default: 0
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

export function getThermalPath(area: string, cluster: string): ThermalPath {
  const pathPrefix = `input/thermal/clusters/${area}/list/${cluster}`;
  return {
    name: `${pathPrefix}/name`,
    group: `${pathPrefix}/group`,
    enabled: `${pathPrefix}/enabled`,
    unitcount: `${pathPrefix}/unitcount`,
    nominalcapacity: `${pathPrefix}/nominalcapacity`,
    genTs: `${pathPrefix}/gen-ts`,
    minStablePower: `${pathPrefix}/min-stable-power`,
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
