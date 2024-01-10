import { snakeCase } from "lodash";
import { DeepPartial } from "react-hook-form";
import { StudyMetadata } from "../../../../common/types";
import client from "../../client";
import { format } from "../../../../utils/stringUtils";
import { TABLE_MODE_API_URL } from "../../constants";
import type { TableData, TableModeColumnsForType, TableModeType } from "./type";

export async function getTableMode<T extends TableModeType>(
  studyId: StudyMetadata["id"],
  type: T,
  columns: TableModeColumnsForType<T>,
): Promise<TableData> {
  const url = format(TABLE_MODE_API_URL, { studyId });
  const res = await client.get(url, {
    params: {
      table_type: type,
      columns: columns.map(snakeCase).join(","),
    },
  });
  return res.data;
}

export function setTableMode(
  studyId: StudyMetadata["id"],
  type: TableModeType,
  data: DeepPartial<TableData>,
): Promise<void> {
  const url = format(TABLE_MODE_API_URL, { studyId });
  return client.put(url, data, {
    params: {
      table_type: type,
    },
  });
}
