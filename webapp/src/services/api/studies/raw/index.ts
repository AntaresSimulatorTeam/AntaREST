import { StudyMetadata } from "../../../../common/types";
import { RAW_API_URL } from "../../constants";
import { format as formatText } from "../../../../utils/stringUtils";
import client from "../../client";

export async function downloadMatrix(
  studyId: StudyMetadata["id"],
  path: string,
  format?: "tsv" | "xlsx",
  header?: boolean,
  index?: boolean,
) {
  const url = `${formatText(RAW_API_URL, { studyId })}/download`;
  const res = await client.get(url, {
    params: {
      path,
      format,
      header,
      index,
    },
  });
  return res.data;
}
