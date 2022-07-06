import * as R from "ramda";

type LinkStyleReturn = [number[], string];

export const linkStyle = R.cond<[string], LinkStyleReturn>([
  [R.equals("dot"), (): LinkStyleReturn => [[1, 5], "round"]],
  [R.equals("dash"), (): LinkStyleReturn => [[16, 8], "square"]],
  [R.equals("dotdash"), (): LinkStyleReturn => [[10, 6, 1, 6], "square"]],
  [R.T, (): LinkStyleReturn => [[0], "butt"]],
]);
