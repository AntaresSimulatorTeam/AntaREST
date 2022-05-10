import * as RA from "ramda-adjunct";
import { RoleType } from "../../common/types";

export const RESERVED_USER_NAMES = ["admin"];
export const RESERVED_GROUP_NAMES = ["admin"];

export const ROLE_TYPE_KEYS = Object.values(RoleType).filter(
  RA.isString
) as (keyof typeof RoleType)[];
