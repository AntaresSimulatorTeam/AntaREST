import { snakeCase } from "lodash";
import { TableModeColumnsForType, TableModeType } from "./type";

export function toColumnApiName(
  column: TableModeColumnsForType<TableModeType>[number],
) {
  if (column === "co2") {
    return "co2";
  }
  return snakeCase(column);
}
