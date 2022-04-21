import * as R from "ramda";

export const RESERVED_USER_NAMES = ["admin"];
export const RESERVED_GROUP_NAMES = ["admin"];

export const sortByName = <T extends { name: string }>(list: T[]): T[] => {
  return R.sortBy<T>(R.compose(R.toLower, R.prop("name")), list);
};
