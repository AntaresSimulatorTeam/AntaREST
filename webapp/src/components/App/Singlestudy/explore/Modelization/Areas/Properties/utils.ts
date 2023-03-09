import { TFunction } from "i18next";
import { getStudyData } from "../../../../../../../services/api/study";
import { transformNameToId } from "../../../../../../../services/utils";
import { rgbToString } from "../../../../../../common/fieldEditors/ColorPickerFE/utils";
import { FilteringType } from "../../../common/types";

type AdequacyPatchMode = "outside" | "inside" | "virtual";

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
  adequacy_patch?: {
    "adequacy-patch"?: {
      "adequacy-patch-mode"?: AdequacyPatchMode;
    };
  };
}

export interface PropertiesFields {
  name: string;
  color: string;
  posX: number;
  posY: number;
  energyCostUnsupplied: number;
  energyCostSpilled: number;
  nonDispatchPower: boolean;
  dispatchHydroPower: boolean;
  otherDispatchPower: boolean;
  filterSynthesis: Array<FilteringType>;
  filterByYear: Array<FilteringType>;
  adequacyPatchMode?: AdequacyPatchMode;
}

export type PropertiesPath = Omit<
  Record<keyof PropertiesFields, string>,
  "name"
>;

export function getPropertiesPath(areaName: string): PropertiesPath {
  const areaId = transformNameToId(areaName);
  const pathPrefix = `input/areas/${areaId}`;
  const optimization = `${pathPrefix}/optimization`;
  const ui = `${pathPrefix}/ui/ui`;
  return {
    color: ui,
    posX: `${ui}/x`,
    posY: `${ui}/y`,
    energyCostUnsupplied: `input/thermal/areas/unserverdenergycost/${areaId}`,
    energyCostSpilled: `input/thermal/areas/spilledenergycost/${areaId}`,
    nonDispatchPower: `${optimization}/nodal optimization/non-dispatchable-power`,
    dispatchHydroPower: `${optimization}/nodal optimization/dispatchable-hydro-power`,
    otherDispatchPower: `${optimization}/nodal optimization/other-dispatchable-power`,
    filterSynthesis: `${optimization}/filtering/filter-synthesis`,
    filterByYear: `${optimization}/filtering/filter-year-by-year`,
    adequacyPatchMode: `${pathPrefix}/adequacy_patch/adequacy-patch/adequacy-patch-mode`,
  };
}

export async function getDefaultValues(
  studyId: string,
  areaName: string,
  t: TFunction<"translation", undefined>
): Promise<PropertiesFields> {
  const areaId = transformNameToId(areaName);
  // Path
  const pathPrefix = `/input/areas/${areaId}`;
  // Fetch fields
  const fields: PropertiesType = await getStudyData(studyId, pathPrefix, 3);
  const energyCostUnsupplied = await getStudyData(
    studyId,
    `input/thermal/areas/unserverdenergycost`,
    1
  );
  const energyCostSpilled = await getStudyData(
    studyId,
    `input/thermal/areas/spilledenergycost`,
    1
  );

  const nodalOptimization: PropertiesType["optimization"]["nodal optimization"] =
    fields.optimization["nodal optimization"];
  const uiElement: PropertiesType["ui"]["ui"] = fields.ui.ui;
  const { filtering } = fields.optimization;

  // Return element
  return {
    name: areaName,
    color: rgbToString({
      r: uiElement.color_r,
      g: uiElement.color_g,
      b: uiElement.color_b,
    }),
    posX: uiElement.x,
    posY: uiElement.y,
    energyCostUnsupplied: energyCostUnsupplied[areaId] || 0,
    energyCostSpilled: energyCostSpilled[areaId] || 0,
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
    ...(fields.adequacy_patch?.["adequacy-patch"]?.["adequacy-patch-mode"] !==
    undefined
      ? {
          adequacyPatchMode:
            fields.adequacy_patch["adequacy-patch"]["adequacy-patch-mode"],
        }
      : {}),
  };
}

export default {};
