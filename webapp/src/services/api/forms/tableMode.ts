import { snakeCase } from "lodash";
import { DeepPartial } from "react-hook-form";
import { StudyMetadata } from "../../../common/types";
import {
  TableData,
  TableTemplateColumnsForType,
  TableTemplateType,
} from "../../../components/App/Singlestudy/explore/Modelization/TableMode/utils";
import client from "../client";

function makeRequestURL(studyId: StudyMetadata["id"]): string {
  return `v1/studies/${studyId}/tablemode/form`;
}

export async function getTableData<T extends TableTemplateType>(
  studyId: StudyMetadata["id"],
  type: T,
  columns: TableTemplateColumnsForType<T>
): Promise<TableData> {
  const res = await client.get(makeRequestURL(studyId), {
    params: {
      table_type: type,
      columns: columns.map(snakeCase).join(","),
    },
  });
  return res.data;
}

export function setTableData(
  studyId: StudyMetadata["id"],
  type: TableTemplateType,
  data: DeepPartial<TableData>
): Promise<void> {
  return client.put(makeRequestURL(studyId), data, {
    params: {
      table_type: type,
    },
  });
}
