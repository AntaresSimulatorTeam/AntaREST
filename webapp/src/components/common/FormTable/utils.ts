import * as R from "ramda";
import * as RA from "ramda-adjunct";

export const getCellType = R.cond([
  [RA.isNumber, R.always("numeric")],
  [RA.isBoolean, R.always("checkbox")],
  [R.T, R.always("text")],
]);
