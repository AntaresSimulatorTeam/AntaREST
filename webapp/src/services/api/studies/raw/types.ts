import type { StudyMetadata } from "../../../../common/types";

export interface DownloadMatrixParams {
  studyId: StudyMetadata["id"];
  path: string;
  format?: "tsv" | "xlsx";
  header?: boolean;
  index?: boolean;
}
