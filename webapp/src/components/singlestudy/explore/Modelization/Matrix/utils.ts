import { Operator } from "./type";

export const Slicer = (tab: any[]) => {
  let newTab = { slices: [], operation: { operation: Operator.EQ, value: 0 } };
  if (tab.length > 1) {
    const tempTab = tab;
    console.log(tempTab);
  } else {
    newTab = {
      slices: [
        {
          row_from: tab[0][0] as number,
          row_to: (tab[0][0] + 1) as number,
          column_from: (tab[0][1] - 1) as number,
          column_to: tab[0][1] as number,
        },
      ],
      operation: {
        operation: Operator.EQ,
        value: parseInt(tab[0][3], 10),
      },
    };
  }
  console.log(newTab);

  return newTab;
};

export default {};
