import { v4 as uuidv4 } from "uuid";

export enum TableTemplateType {
  Area = "area",
  Link = "link",
  Cluster = "cluster",
}

export const TABLE_TEMPLATE_TYPE_OPTIONS = Object.values(TableTemplateType);

const TABLE_TEMPLATE_COLUMNS_BY_TYPE = {
  [TableTemplateType.Area]: [
    // Optimization - Nodal optimization
    "nonDispatchablePower",
    "dispatchableHydroPower",
    "otherDispatchablePower",
    "spreadUnsuppliedEnergyCost",
    "spreadSpilledEnergyCost",
    // Optimization - Filtering
    "filterSynthesis",
    "filterYearByYear",
    // Adequacy patch
    "adequacyPatchMode",
  ],
  [TableTemplateType.Link]: [
    "hurdlesCost",
    "loopFlow",
    "usePhaseShifter",
    "transmissionCapacities",
    "assetType",
    "linkStyle",
    "linkWidth",
    "displayComments",
    "filterSynthesis",
    "filterYearByYear",
  ],
  [TableTemplateType.Cluster]: [
    "group",
    "enabled",
    "mustRun",
    "unitCount",
    "nominalCapacity",
    "minStablePower",
    "spinning",
    "minUpTime",
    "minDownTime",
    "co2",
    "marginalCost",
    "fixedCost",
    "startupCost",
    "marketBidCost",
    "spreadCost",
    "tsGen",
    "volatilityForced",
    "volatilityPlanned",
    "lawForced",
    "lawPlanned",
  ],
} as const;

export type TableTemplateColumnsForType<T extends TableTemplateType> = Array<
  typeof TABLE_TEMPLATE_COLUMNS_BY_TYPE[T][number]
>;

export interface TableTemplate<
  T extends TableTemplateType = TableTemplateType
> {
  id: string;
  name: string;
  type: T;
  columns: TableTemplateColumnsForType<T>;
}

/**
 * Allows to check columns validity for specified type.
 */
export function createTableTemplate<T extends TableTemplateType>(
  name: string,
  type: T,
  columns: TableTemplateColumnsForType<T>
): TableTemplate<T> {
  return { id: uuidv4(), name, type, columns };
}

export const DEFAULT_TABLE_TEMPLATES: TableTemplate[] = [
  createTableTemplate("economicOpt", TableTemplateType.Area, [
    "spreadUnsuppliedEnergyCost",
    "spreadSpilledEnergyCost",
    "nonDispatchablePower",
    "dispatchableHydroPower",
    "otherDispatchablePower",
  ]),
  createTableTemplate("geographicTrimmingAreas", TableTemplateType.Area, [
    "filterYearByYear",
    "filterSynthesis",
  ]),
  createTableTemplate("geographicTrimmingLinks", TableTemplateType.Link, [
    "filterYearByYear",
    "filterSynthesis",
  ]),
];

export const DEFAULT_TABLE_TEMPLATE_IDS = DEFAULT_TABLE_TEMPLATES.map(
  (t) => t.id
);

export function getTableColumnsForType(type: TableTemplateType): string[] {
  // Arrays have a numeric index signature because of `as const`
  return Object.values(TABLE_TEMPLATE_COLUMNS_BY_TYPE[type]);
}

export type TableData = Record<
  string,
  Record<string, string | boolean | number>
>;
