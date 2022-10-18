export enum TableTemplateType {
  Area = "area",
  Link = "link",
  Cluster = "cluster",
  BindingConstraint = "bindingConstraint",
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
  [TableTemplateType.BindingConstraint]: [],
} as const;

export type TableTemplateColumnsForType<T extends TableTemplateType> = Array<
  typeof TABLE_TEMPLATE_COLUMNS_BY_TYPE[T][number]
>;

export interface TableTemplate<
  T extends TableTemplateType = TableTemplateType
> {
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
  return { name, type, columns };
}

export const DEFAULT_TABLE_TEMPLATES: TableTemplate[] = [
  createTableTemplate("Economic Opt.", TableTemplateType.Area, [
    "spreadUnsuppliedEnergyCost",
    "spreadSpilledEnergyCost",
    "nonDispatchablePower",
    "dispatchableHydroPower",
    "otherDispatchablePower",
  ]),
];

export const DEFAULT_TABLE_TEMPLATE_NAMES = DEFAULT_TABLE_TEMPLATES.map(
  (t) => t.name
);

export function getTableColumnsForType(type: TableTemplateType): string[] {
  // Arrays have a numeric index signature because of `as const`
  return Object.values(TABLE_TEMPLATE_COLUMNS_BY_TYPE[type]);
}

export type TableData = Record<
  string,
  Record<string, string | boolean | number>
>;
