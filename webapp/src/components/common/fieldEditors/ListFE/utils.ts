import { v4 as uuidv4 } from "uuid";
import * as RA from "ramda-adjunct";

export function makeListItems<T>(
  value: ReadonlyArray<T>
): Array<{ id: string; value: T }> {
  return value.map((v) => ({ id: uuidv4(), value: v }));
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function makeLabel(value: any): string {
  // Default value for `getOptionLabel` prop in Autocomplete
  if (RA.isString(value?.label)) {
    return value.label;
  }
  return value?.toString() ?? "";
}
