import type {
  GetThematicTrimmingConfigParams,
  SetThematicTrimmingConfigParams,
  ThematicTrimmingConfig,
} from "./types";
import client from "../../../client";
import { format } from "../../../../../utils/stringUtils";

const URL = "/v1/studies/{studyId}/config/thematictrimming/form";

export async function getThematicTrimmingConfig({
  studyId,
}: GetThematicTrimmingConfigParams) {
  const url = format(URL, { studyId });
  const res = await client.get<ThematicTrimmingConfig>(url);
  return res.data;
}

export async function setThematicTrimmingConfig({
  studyId,
  config,
}: SetThematicTrimmingConfigParams) {
  const url = format(URL, { studyId });
  await client.put(url, config);
}
