import { FieldValues } from "react-hook-form";
import {
  Area,
  Cluster,
  StudyMetadata,
} from "../../../../../../../common/types";
import client from "../../../../../../../services/api/client";
import { getStudyData } from "../../../../../../../services/api/study";

export interface ThermalType extends FieldValues {
  name: string;
  group: string;
  enabled?: boolean;
  unitcount?: number;
  nominalcapacity?: number;
  "gen-ts"?: string;
  "min-stable-power"?: number;
  "min-up-time"?: number;
  "min-down-time"?: number;
  "must-run"?: boolean;
  spinning?: number;
  co2?: number;
  "volatility.forced"?: number;
  "volatility.planned"?: number;
  "law.forced"?: string;
  "law.planned"?: string;
  "marginal-cost"?: number;
  "spread-cost"?: number;
  "fixed-cost"?: number;
  "startup-cost"?: number;
  "market-bid-cost"?: number;
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

////////////////////////////////////////////////////////////////
// Enums
////////////////////////////////////////////////////////////////

enum ClusterGroup {
  Gas = "Gas",
  HardCoal = "Hard Coal",
  Lignite = "Lignite",
  MixedFuel = "Mixed fuel",
  Nuclear = "Nuclear",
  Oil = "Oil",
  Other = "Other",
  Other2 = "Other 2",
  Other3 = "Other 3",
  Other4 = "Other 4",
}

enum TimeSeriesGeneration {
  Global = "use global parameter",
  NoGeneration = "force no generation",
  Generation = "force generation",
}

enum TimeSeriesLaw {
  Geometric = "geometric",
  Uniform = "uniform",
}

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export interface ThermalFormFields {
  name: string;
  group: string;
  enabled: boolean;
  unitCount: number;
  nominalCapacity: number;
  mustRun: boolean;
  minStablePower: number;
  spinning: number;
  minUpTime: number;
  minDownTime: number;
  co2: number;
  marginalCost: number;
  fixedCost: number;
  startupCost: number;
  marketBidCost: number;
  spreadCost: number;
  genTs: TimeSeriesGeneration;
  volatilityForced: number;
  volatilityPlanned: number;
  lawForced: TimeSeriesLaw;
  lawPlanned: TimeSeriesLaw;
}

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const CLUSTER_GROUP_OPTIONS = Object.values(ClusterGroup);
export const TS_GENERATION_OPTIONS = Object.values(TimeSeriesGeneration);
export const TS_LAW_OPTIONS = Object.values(TimeSeriesLaw);

////////////////////////////////////////////////////////////////
// Utils
////////////////////////////////////////////////////////////////

function makeRequestURL(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"]
): string {
  return `/v1/studies/${studyId}/areas/${areaId}/clusters/thermal/${clusterId}/form`;
}

export async function getThermalFormFields(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"]
): Promise<ThermalFormFields> {
  const res = await client.get(makeRequestURL(studyId, areaId, clusterId));
  return res.data;
}

export function updateThermalFormFields(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
  values: Partial<ThermalFormFields>
): Promise<void> {
  return client.put(makeRequestURL(studyId, areaId, clusterId), values);
}
