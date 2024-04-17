import client from "../../client";
import { format } from "../../../../utils/stringUtils";
import type {
  GetTableModeParams,
  SetTableModeParams,
  TableData,
  TableModeType,
} from "./types";
import { toColumnApiName } from "./utils";

const TABLE_MODE_API_URL = `v1/studies/{studyId}/tablemode`;

export async function getTableMode<T extends TableModeType>(
  params: GetTableModeParams<T>,
) {
  const { studyId, type, columns } = params;
  const url = format(TABLE_MODE_API_URL, { studyId });

  const res = await client.get<TableData>(url, {
    params: {
      table_type: type,
      columns: columns.map(toColumnApiName).join(","),
    },
  });

  return res.data;
}

export async function setTableMode(params: SetTableModeParams) {
  const { studyId, type, data } = params;
  const url = format(TABLE_MODE_API_URL, { studyId });

  await client.put<null>(url, data, {
    params: { table_type: type },
  });
}
