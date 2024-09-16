import client from "../../client";
import type { DownloadMatrixParams, ImportFileParams } from "./types";

export async function downloadMatrix(params: DownloadMatrixParams) {
  const { studyId, ...queryParams } = params;
  const url = `v1/studies/${studyId}/raw/download`;
  const res = await client.get<Blob>(url, {
    params: queryParams,
    responseType: "blob",
  });

  return res.data;
}

export async function importFile(params: ImportFileParams) {
  const { studyId, file, onUploadProgress, ...queryParams } = params;
  const url = `v1/studies/${studyId}/raw`;
  const body = { file };
  await client.putForm<void>(url, body, {
    params: {
      ...queryParams,
      create_missing: queryParams.createMissing,
    },
    onUploadProgress,
  });
}
