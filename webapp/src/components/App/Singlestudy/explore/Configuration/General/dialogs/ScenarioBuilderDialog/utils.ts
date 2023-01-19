import { AxiosResponse } from "axios";
import { StudyMetadata } from "../../../../../../../../common/types";
import client from "../../../../../../../../services/api/client";

export const TABS_DATA: Array<[string, string]> = [
  ["load", "l"],
  ["thermal", "t"],
  ["hydro", "h"],
  ["wind", "w"],
  ["solar", "s"],
  ["ntc", "ntc"],
  ["hydroLevels", "hl"],
];

export const ACTIVE_SCENARIO_PATH =
  "settings/generaldata/general/active-rules-scenario";

export type ScenarioBuilderConfig = Record<string, unknown>;

function makeRequestURL(studyId: StudyMetadata["id"]): string {
  return `v1/studies/${studyId}/config/scenariobuilder`;
}

export async function getScenarioBuilderConfig(
  studyId: StudyMetadata["id"]
): Promise<ScenarioBuilderConfig> {
  const res = await client.get(makeRequestURL(studyId));
  return res.data;
}

export async function updateScenarioBuilderConfig(
  studyId: StudyMetadata["id"],
  data: Partial<ScenarioBuilderConfig>
): Promise<AxiosResponse<null, string>> {
  return client.put(makeRequestURL(studyId), data);
}
