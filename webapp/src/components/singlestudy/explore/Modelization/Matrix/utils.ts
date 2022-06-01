import { CellChange, MatrixEditDTO, MatrixSlice, Operator } from "./type";

export const slice = (tab: CellChange[]): MatrixEditDTO[] => {
  let newTab = {
    slices: [
      {
        row_from: 0,
        row_to: 0,
        column_from: 1,
        column_to: 2,
      },
    ],
    operation: { operation: Operator.EQ, value: 0 },
  };
  if (tab.length > 1) {
    const tempSlices: MatrixSlice[] = [
      {
        row_from: tab[0][0],
        row_to: tab[0][0] + 1,
        column_from: (tab[0][1] as number) - 1,
        column_to: tab[0][1] as number,
      },
    ];
    let test: MatrixSlice[] = tempSlices;
    for (let i = 0; i < tab.length; i += 1) {
      if (i + 1 < tab.length && tab[0][0] === tab[i + 1][0]) {
        test = [
          ...test,
          ...[
            {
              row_from: tab[i + 1][0] as number,
              row_to: (tab[i + 1][0] as number) + 1,
              column_from: (tab[i + 1][1] as number) - 1,
              column_to: tab[i + 1][1] as number,
            },
          ],
        ];
      } else if (i + 1 < tab.length && tab[0][1] === tab[i + 1][1]) {
        test = [
          ...test,
          ...[
            {
              row_from: tab[i + 1][0] as number,
              row_to: (tab[i + 1][0] as number) + 1,
              column_from: (tab[i + 1][1] as number) - 1,
              column_to: tab[i + 1][1] as number,
            },
          ],
        ];
      }
    }
    newTab = {
      slices: test,
      operation: { operation: Operator.EQ, value: parseInt(tab[0][3], 10) },
    };
  } else {
    newTab = {
      slices: [
        {
          row_from: 0,
          row_to: 0,
          column_from: 1,
          column_to: 2,
        },
      ],
      operation: {
        operation: Operator.EQ,
        value: parseInt(tab[0][3], 10),
      },
    };
  }
  return [newTab];
};

export default {};
