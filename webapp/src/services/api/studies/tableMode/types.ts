import { DeepPartial } from "react-hook-form";
import type { StudyMetadata } from "../../../../common/types";
import { TABLE_MODE_COLUMNS_BY_TYPE, TABLE_MODE_TYPES } from "./constants";

export type TableModeType = (typeof TABLE_MODE_TYPES)[number];

export type TableModeColumnsForType<T extends TableModeType> = Array<
  (typeof TABLE_MODE_COLUMNS_BY_TYPE)[T][number]
>;

export type TableData = Record<
  string,
  Record<string, string | boolean | number>
>;

export interface GetTableModeParams<T extends TableModeType> {
  studyId: StudyMetadata["id"];
  type: T;
  columns: TableModeColumnsForType<T>;
}

export interface SetTableModeParams {
  studyId: StudyMetadata["id"];
  type: TableModeType;
  data: DeepPartial<TableData>;
}
