import type { AxiosRequestConfig } from "axios";
import type { StudyMetadata } from "../../../../common/types";

export interface DownloadMatrixParams {
  studyId: StudyMetadata["id"];
  path: string;
  format?: "tsv" | "xlsx";
  header?: boolean;
  index?: boolean;
}

export interface ImportFileParams {
  studyId: StudyMetadata["id"];
  path: string;
  file: File;
  createMissing?: boolean;
  onUploadProgress?: AxiosRequestConfig["onUploadProgress"];
}

export interface DeleteFileParams {
  studyId: StudyMetadata["id"];
  path: string;
}
