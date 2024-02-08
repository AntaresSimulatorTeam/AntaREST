import { v4 as uuidv4 } from "uuid";
import {
  TableModeColumnsForType,
  TableModeType,
} from "../../../../../services/api/studies/tableMode/type";
import { TABLE_MODE_COLUMNS_BY_TYPE } from "../../../../../services/api/studies/tableMode/constants";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export interface TableTemplate<T extends TableModeType = TableModeType> {
  id: string;
  name: string;
  type: T;
  columns: TableModeColumnsForType<T>;
}

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

/**
 * Allows to check columns validity for specified type.
 */
export function createTableTemplate<T extends TableModeType>(
  name: string,
  type: T,
  columns: TableModeColumnsForType<T>,
): TableTemplate<T> {
  return { id: uuidv4(), name, type, columns };
}

export function getTableColumnsForType(type: TableModeType): readonly string[] {
  // Arrays have a numeric index signature because of `as const`
  return TABLE_MODE_COLUMNS_BY_TYPE[type];
}
