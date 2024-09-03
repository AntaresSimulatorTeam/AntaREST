import {
  BaseGridColumn,
  FillPatternEventArgs,
} from "@glideapps/glide-data-grid";
import { ColumnDataType } from "./utils";

export interface MatrixData {
  data: number[][];
  columns: number[];
  index: number[];
}

export type ColumnType = (typeof ColumnDataType)[keyof typeof ColumnDataType];

export interface EnhancedGridColumn extends BaseGridColumn {
  id: string;
  width?: number;
  type: ColumnType;
  editable: boolean;
}

export type CellFillPattern = Omit<FillPatternEventArgs, "preventDefault">;

// TODO see MatrixIndex type, rundundant types
export interface TimeMetadataDTO {
  start_date: string;
  steps: number;
  first_week_size: number;
  level: "hourly" | "daily" | "weekly" | "monthly" | "yearly";
}

export type DateIncrementStrategy = (
  date: moment.Moment,
  step: number,
) => moment.Moment;
