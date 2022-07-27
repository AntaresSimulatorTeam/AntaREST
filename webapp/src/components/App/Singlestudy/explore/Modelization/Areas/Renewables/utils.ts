import { FieldValues } from "react-hook-form";

type TsModeType = "power generation" | "production factor";

export interface RenewableType extends FieldValues {
  name: string;
  group?: string;
  "ts-interpretation": TsModeType;
  enabled: boolean; // Default: true
  unitcount: number; // Default: 0
  nominalcapacity: number; // Default: 0
}

export const noDataValues: Partial<RenewableType> = {
  enabled: true,
  unitcount: 0,
  nominalcapacity: 0,
};

export const tsModeOptions = ["power generation", "production factor"].map(
  (item) => ({
    label: item,
    value: item,
  })
);

export const fixedGroupList = [
  "Wind Onshore",
  "Wind Offshore",
  "Solar Thermal",
  "Solar PV",
  "Solar Rooftop",
  "Other RES 1",
  "Other RES 2",
  "Other RES 3",
  "Other RES 4",
];

export type RenewablePath = Record<keyof RenewableType, string>;
