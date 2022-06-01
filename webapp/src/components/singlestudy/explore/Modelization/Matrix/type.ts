export enum Operator {
  ADD = "+",
  SUB = "-",
  MUL = "*",
  DIV = "/",
  ABS = "ABS",
  EQ = "=",
}

export interface MatrixSlice {
  row_from: number;
  row_to: number;
  column_from: number;
  column_to: number;
}

export interface MatrixOperation {
  operation: Operator;
  value: number;
}

export interface MatrixEditDTO {
  slices: MatrixSlice[];
  operation: MatrixOperation;
}

export interface CellChange {
  "0": number;
  "1": number | string;
  "2": number;
  "3": string;
}

export default {};
