import { Area, LinkElement, Simulation } from "../../../../../../common/types";

export enum OutputItemType {
  Areas = "areas",
  Links = "links",
}

export enum DataType {
  General = "values",
  Thermal = "details",
  Renewable = "details-res",
  Record = "id",
}

export enum Timestep {
  Hourly = "hourly",
  Daily = "daily",
  Weekly = "weekly",
  Monthly = "monthly",
  Annual = "annual",
}

interface Params {
  output: Simulation & { id: string };
  item: (Area & { id: string }) | LinkElement;
  dataType: DataType;
  timestep: Timestep;
  year?: number;
}

export const MAX_YEAR = 99999;

export function createPath(params: Params): string {
  const { output, item, dataType, timestep, year } = params;
  const { id, mode } = output;
  const isYearPeriod = year && year > 0;
  const periodFolder = isYearPeriod
    ? `mc-ind/${Math.max(year, output.nbyears).toString().padStart(5, "0")}`
    : "mc-all";
  const isLink = "area1" in item;
  const itemType = isLink ? OutputItemType.Links : OutputItemType.Areas;
  const itemFolder = isLink ? `${item.area1}/${item.area2}` : item.id;

  return `output/${id}/${mode}/${periodFolder}/${itemType}/${itemFolder}/${dataType}-${timestep}`;
}
