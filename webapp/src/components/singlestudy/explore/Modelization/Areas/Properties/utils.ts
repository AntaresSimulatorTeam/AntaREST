import { getStudyData } from "../../../../../../services/api/study";
import { FieldElement, FieldsInfo } from "./common";

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

export interface PropertiesFields extends FieldsInfo {
  name: FieldElement<string>;
  color_r: FieldElement<number>;
  color_g: FieldElement<number>;
  color_b: FieldElement<number>;
  posX: FieldElement<number>;
  posY: FieldElement<number>;
  energieCostUnsupplied: FieldElement<number>;
  energieCostSpilled: FieldElement<number>;
  nonDispatchPower: FieldElement<boolean>;
  dispatchHydroPower: FieldElement<boolean>;
  otherDispatchPower: FieldElement<boolean>;
}

export async function getDefaultValues(
  studyId: string,
  areaName: string
): Promise<PropertiesFields> {
  // Path
  const pathPrefix = `input/areas/${areaName.toLowerCase()}`;
  const pathOptimization = `${pathPrefix}/optimization`;
  const pathUI = `${pathPrefix}/ui`;

  // Fetch fields
  const fields: PropertiesType = await getStudyData(studyId, pathPrefix);
  const nodalOptimization: PropertiesType["optimization"]["nodal optimization"] =
    fields.optimization["nodal optimization"];
  const uiElement: PropertiesType["ui"]["ui"] = fields.ui.ui;

  // Return element
  return {
    name: { value: areaName },
    color_r: { value: uiElement.color_r, path: `${pathUI}/ui/color_r` },
    color_g: { value: uiElement.color_g, path: `${pathUI}/ui/color_g` },
    color_b: { value: uiElement.color_b, path: `${pathUI}/ui/color_b` },
    posX: { value: uiElement.x, path: `${pathUI}/ui/x` },
    posY: { value: uiElement.y, path: `${pathUI}/ui/y` },
    energieCostUnsupplied: {
      value: nodalOptimization["spread-unsupplied-energy-cost"],
      path: `${pathOptimization}/nodal optimization/spread-unsupplied-energy-cost`,
    },
    energieCostSpilled: {
      value: nodalOptimization["spread-spilled-energy-cost"],
      path: `${pathOptimization}/nodal optimization/spread-spilled-energy-cost`,
    },
    nonDispatchPower: {
      value: nodalOptimization["non-dispatchable-power"],
      path: `${pathOptimization}/nodal optimization/non-dispatchable-power`,
    },
    dispatchHydroPower: {
      value: nodalOptimization["dispatchable-hydro-power"],
      path: `${pathOptimization}/nodal optimization/dispatchable-hydro-power`,
    },
    otherDispatchPower: {
      value: nodalOptimization["other-dispatchable-power"],
      path: `${pathOptimization}/nodal optimization/other-dispatchable-power`,
    },
  };
}

export default {};
