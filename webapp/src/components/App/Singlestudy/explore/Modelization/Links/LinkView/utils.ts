import { FieldValues } from "react-hook-form";
import { getStudyData } from "../../../../../../../services/api/study";

type TransCapacitiesType = "infinite" | "ignore" | "enabled";
type AssetType = "ac" | "dc" | "gaz" | "virt";
type LinkStyleType = "plain" | "dash" | "dot" | "dotdash";
type FilteringType = "hourly" | "daily" | "weekly" | "monthly" | "annual";

export interface LinkType {
  "hurdles-cost": boolean;
  "loop-flow": boolean;
  "use-phase-shifter": boolean;
  "transmission-capacities": TransCapacitiesType;
  "asset-type": AssetType;
  "link-style": LinkStyleType;
  "link-width": number;
  colorr: number;
  colorg: number;
  colorb: number;
  "filter-synthesis": string;
  "filter-year-by-year": string;
}

export interface LinkFields extends FieldValues {
  hurdleCost: boolean;
  loopFlows: boolean;
  pst: boolean;
  type: string;
  transmissionCapa: string;
  filterSynthesis: Array<FilteringType>;
  filterByYear: Array<FilteringType>;
}

export type LinkPath = Omit<Record<keyof LinkFields, string>, "name">;

export function getLinkPath(area1: string, area2: string): LinkPath {
  const pathPrefix = `input/links/${area1.toLowerCase()}/properties/${area2.toLowerCase()}`;
  return {
    hurdleCost: `${pathPrefix}/hurdles-cost`,
    loopFlows: `${pathPrefix}/loop-flow`,
    pst: `${pathPrefix}/use-phase-shifter`,
    type: pathPrefix,
    transmissionCapa: `${pathPrefix}/transmission-capacities`,
    filterSynthesis: `${pathPrefix}/filter-synthesis`,
    filterByYear: `${pathPrefix}/filter-year-by-year`,
  };
}

export async function getDefaultValues(
  studyId: string,
  area1: string,
  area2: string
): Promise<LinkFields> {
  // Path
  const pathPrefix = `input/links/${area1.toLowerCase()}/properties/${area2.toLowerCase()}`;
  // Fetch fields
  const fields: LinkType = await getStudyData(studyId, pathPrefix, 3);

  // Return element
  return {
    hurdleCost: fields["hurdles-cost"],
    loopFlows: fields["loop-flow"],
    pst: fields["use-phase-shifter"],
    type: fields["asset-type"],
    transmissionCapa: fields["transmission-capacities"],
    filterSynthesis: fields["filter-synthesis"].split(",").map((elm) => {
      const sElm = elm.replace(/\s+/g, "");
      return sElm as FilteringType;
    }),
    filterByYear: fields["filter-year-by-year"].split(",").map((elm) => {
      const sElm = elm.replace(/\s+/g, "");
      return sElm as FilteringType;
    }),
  };
}

export default {};
