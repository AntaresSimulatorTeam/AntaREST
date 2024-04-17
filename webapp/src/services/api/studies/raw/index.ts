import client from "../../client";
import type { DownloadMatrixParams } from "./types";

export async function downloadMatrix(params: DownloadMatrixParams) {
  const { studyId, ...rest } = params;
  const url = `v1/studies/${studyId}/raw/download`;
  const res = await client.get<Blob>(url, {
    params: rest,
    responseType: "blob",
  });

  return res.data;
}
