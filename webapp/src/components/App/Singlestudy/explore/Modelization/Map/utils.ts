import * as R from "ramda";

export const linkStyle = (linkStyle: string): Array<Array<number> | string> => {
  const linkCond = R.cond([
    [
      R.equals("dot"),
      (): Array<Array<number> | string> => {
        return [[1, 5], "round"];
      },
    ],
    [
      R.equals("dash"),
      (): Array<Array<number> | string> => {
        return [[16, 8], "square"];
      },
    ],
    [
      R.equals("dotdash"),
      (): Array<Array<number> | string> => {
        return [[10, 6, 1, 6], "square"];
      },
    ],
    [
      (_: string): boolean => true,
      (): Array<Array<number> | string> => {
        return [[0], "butt"];
      },
    ],
  ]);

  const values = linkCond(linkStyle);
  const style = values[0] as Array<number>;
  const linecap = values[1] as string;

  return [style, linecap];
};

export default {};
