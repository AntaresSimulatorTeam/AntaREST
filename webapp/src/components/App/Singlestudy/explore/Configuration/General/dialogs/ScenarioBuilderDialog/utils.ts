import { StudyMetadata } from "../../../../../../../../common/types";
import client from "../../../../../../../../services/api/client";

export async function getScenarioBuilderConfig(
  studyId: StudyMetadata["id"]
): Promise<any> {
  const res = await client.get(`v1/studies/${studyId}/config/scenariobuilder`);
  return res.data;
}

export async function setScenarioBuilderConfig(
  studyId: StudyMetadata["id"],
  config: any
): Promise<any> {
  return client.put(`v1/studies/${studyId}/config/scenariobuilder`, config);
}
