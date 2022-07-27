import { deburr } from "lodash";
import * as R from "ramda";
import * as RA from "ramda-adjunct";

export const isSearchMatching = R.curry(
  (search: string, values: string | string[]) => {
    const format = R.o(R.toLower, deburr);
    const isMatching = R.o(R.includes(format(search)), format);
    return RA.ensureArray(values).find(isMatching);
  }
);
