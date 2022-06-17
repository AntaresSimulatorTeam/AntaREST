import { FieldValues } from "react-hook-form";
import { TFunction } from "react-i18next";
import { getStudyData } from "../../../../../../../services/api/study";
import { RGBToString } from "../../../../../../common/fieldEditors/ColorPickerFE/utils";

export interface PropertiesType {
  ui: {
    ui: {
      x: number;
      y: number;
      color_r: number;
      color_g: number;
      color_b: number;
    };
  };
  optimization: {
    "nodal optimization": {
      "non-dispatchable-power": boolean;
      "dispatchable-hydro-power": boolean;
      "other-dispatchable-power": boolean;
      "spread-unsupplied-energy-cost": number;
      "spread-spilled-energy-cost": number;
    };
    filtering: {
      "filter-synthesis": string;
      "filter-year-by-year": string; // "hourly, daily, weekly, monthly, annual";
    };
  };
}

type FilteringType = "hourly" | "daily" | "weekly" | "monthly" | "annual";

export interface PropertiesFields extends FieldValues {
  name: string;
  color: string;
  posX: number;
  posY: number;
  energieCostUnsupplied: number;
  energieCostSpilled: number;
  nonDispatchPower: boolean;
  dispatchHydroPower: boolean;
  otherDispatchPower: boolean;
  filterSynthesis: Array<FilteringType>;
  filterByYear: Array<FilteringType>;
}

export type PropertiesPath = Omit<
  Record<keyof PropertiesFields, string>,
  "name"
>;

export function getPropertiesPath(areaName: string): PropertiesPath {
  const pathPrefix = `input/areas/${areaName.toLowerCase()}`;
  const optimization = `${pathPrefix}/optimization`;
  const ui = `${pathPrefix}/ui/ui`;
  return {
    color: ui,
    posX: `${ui}/x`,
    posY: `${ui}/y`,
    energieCostUnsupplied: `${optimization}/nodal optimization/spread-unsupplied-energy-cost`,
    energieCostSpilled: `${optimization}/nodal optimization/spread-spilled-energy-cost`,
    nonDispatchPower: `${optimization}/nodal optimization/non-dispatchable-power`,
    dispatchHydroPower: `${optimization}/nodal optimization/dispatchable-hydro-power`,
    otherDispatchPower: `${optimization}/nodal optimization/other-dispatchable-power`,
    filterSynthesis: `${optimization}/filtering/filter-synthesis`,
    filterByYear: `${optimization}/filtering/filter-year-by-year`,
  };
}

export async function getDefaultValues(
  studyId: string,
  areaName: string,
  t: TFunction<"translation", undefined>
): Promise<PropertiesFields> {
  // Path
  const pathPrefix = `/input/areas/${areaName.toLowerCase()}`;
  // Fetch fields
  const fields: PropertiesType = await getStudyData(studyId, pathPrefix, 3);
  const nodalOptimization: PropertiesType["optimization"]["nodal optimization"] =
    fields.optimization["nodal optimization"];
  const uiElement: PropertiesType["ui"]["ui"] = fields.ui.ui;
  const { filtering } = fields.optimization;

  // Return element
  return {
    name: areaName,
    color: RGBToString({
      r: uiElement.color_r,
      g: uiElement.color_g,
      b: uiElement.color_b,
    }),
    posX: uiElement.x,
    posY: uiElement.y,
    energieCostUnsupplied: nodalOptimization["spread-unsupplied-energy-cost"],
    energieCostSpilled: nodalOptimization["spread-spilled-energy-cost"],
    nonDispatchPower: nodalOptimization["non-dispatchable-power"],
    dispatchHydroPower: nodalOptimization["dispatchable-hydro-power"],
    otherDispatchPower: nodalOptimization["other-dispatchable-power"],
    filterSynthesis: filtering["filter-synthesis"].split(",").map((elm) => {
      const sElm = elm.replace(/\s+/g, "");
      return sElm as FilteringType;
    }),
    filterByYear: filtering["filter-year-by-year"].split(",").map((elm) => {
      const sElm = elm.replace(/\s+/g, "");
      return sElm as FilteringType;
    }),
  };
}

export default {};
