import client from "../../client";
import { format } from "../../../../utils/stringUtils";
import type {
  GetTableModeParams,
  SetTableModeParams,
  TableData,
  TableModeType,
} from "./types";

const TABLE_MODE_API_URL = `v1/studies/{studyId}/table-mode/{tableType}`;

export async function getTableMode<T extends TableModeType>(
  params: GetTableModeParams<T>,
) {
  const { studyId, tableType, columns } = params;
  const url = format(TABLE_MODE_API_URL, { studyId, tableType });

  const res = await client.get<TableData>(url, {
    params: columns.length > 0 ? { columns: columns.join(",") } : {},
  });

  return res.data;
}

export async function setTableMode(params: SetTableModeParams) {
  const { studyId, tableType, data } = params;
  const url = format(TABLE_MODE_API_URL, { studyId, tableType });
  await client.put<null>(url, data);
}
