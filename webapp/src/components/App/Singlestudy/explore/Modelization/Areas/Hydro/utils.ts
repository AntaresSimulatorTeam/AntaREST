import { MatrixStats, MatrixType } from "../../../../../../../common/types";
import { SplitViewProps } from "../../../../../../common/SplitView";
import { getAllocationMatrix } from "./Allocation/utils";
import { getCorrelationMatrix } from "./Correlation/utils";

////////////////////////////////////////////////////////////////
// Enums
////////////////////////////////////////////////////////////////

export enum HydroMatrixType {
  Dailypower,
  EnergyCredits,
  ReservoirLevels,
  WaterValues,
  HydroStorage,
  RunOfRiver,
  InflowPattern,
  OverallMonthlyHydro,
  Allocation,
  Correlation,
}

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export type fetchMatrixFn = (studyId: string) => Promise<MatrixType>;

export interface HydroMatrixProps {
  title: string;
  url: string;
  cols?: string[];
  rows?: string[];
  stats: MatrixStats;
  fetchFn?: fetchMatrixFn;
  disableEdit?: boolean;
  enablePercentDisplay?: boolean;
}

type Matrices = Record<HydroMatrixType, HydroMatrixProps>;

export interface HydroRoute {
  path: string;
  type: number;
  isSplitView?: boolean;
  splitConfig?: {
    direction: SplitViewProps["direction"];
    partnerType: HydroMatrixType;
    sizes: SplitViewProps["sizes"];
  };
}

export interface AreaCoefficientItem {
  areaId: string;
  coefficient: number;
}

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const HYDRO_ROUTES: HydroRoute[] = [
  {
    path: "inflowstructure",
    type: HydroMatrixType.InflowPattern,
    isSplitView: true,
    splitConfig: {
      direction: "horizontal",
      partnerType: HydroMatrixType.OverallMonthlyHydro,
      sizes: [50, 50],
    },
  },
  {
    path: "dailypower&energy",
    type: HydroMatrixType.Dailypower,
    isSplitView: true,
    splitConfig: {
      direction: "vertical",
      partnerType: HydroMatrixType.EnergyCredits,
      sizes: [25, 75],
    },
  },
  {
    path: "reservoirlevels",
    type: HydroMatrixType.ReservoirLevels,
  },
  {
    path: "watervalues",
    type: HydroMatrixType.WaterValues,
  },
  {
    path: "hydrostorage",
    type: HydroMatrixType.HydroStorage,
  },
  {
    path: "ror",
    type: HydroMatrixType.RunOfRiver,
  },
];

export const MATRICES: Matrices = {
  [HydroMatrixType.Dailypower]: {
    title: "Credit Modulation",
    url: "input/hydro/common/capacity/creditmodulations_{areaId}",
    cols: generateColumns("%"),
    rows: ["Generating Power", "Pumping Power"],
    stats: MatrixStats.NOCOL,
    enablePercentDisplay: true,
  },
  [HydroMatrixType.EnergyCredits]: {
    title: "Standard Credit",
    url: "input/hydro/common/capacity/maxpower_{areaId}",
    cols: [
      "Generating Max Power (MW)",
      "Generating Max Energy (Hours at Pmax)",
      "Pumping Max Power (MW)",
      "Pumping Max Energy (Hours at Pmax)",
    ],
    stats: MatrixStats.NOCOL,
  },
  [HydroMatrixType.ReservoirLevels]: {
    title: "Reservoir Levels",
    url: "input/hydro/common/capacity/reservoir_{areaId}",
    cols: ["Lev Low (%)", "Lev Avg (%)", "Lev High (%)"],
    stats: MatrixStats.NOCOL,
    enablePercentDisplay: true,
  },
  [HydroMatrixType.WaterValues]: {
    title: "Water Values",
    url: "input/hydro/common/capacity/waterValues_{areaId}",
    cols: generateColumns("%"),
    stats: MatrixStats.NOCOL,
  },
  [HydroMatrixType.HydroStorage]: {
    title: "Hydro Storage",
    url: "input/hydro/series/{areaId}/mod",
    stats: MatrixStats.STATS,
  },
  [HydroMatrixType.RunOfRiver]: {
    title: "Run Of River",
    url: "input/hydro/series/{areaId}/ror",
    stats: MatrixStats.STATS,
  },
  [HydroMatrixType.InflowPattern]: {
    title: "Inflow Pattern",
    url: "input/hydro/common/capacity/inflowPattern_{areaId}",
    cols: ["Inflow Pattern (X)"],
    stats: MatrixStats.NOCOL,
  },
  [HydroMatrixType.OverallMonthlyHydro]: {
    title: "Overall Monthly Hydro",
    url: "input/hydro/prepro/{areaId}/energy",
    cols: [
      "Expectation (MWh)",
      "Std Deviation (MWh)",
      "Min. (MWh)",
      "Max. (MWh)",
      "ROR Share",
    ],
    rows: [
      "January",
      "February",
      "March",
      "April",
      "May",
      "June",
      "July",
      "August",
      "September",
      "October",
      "November",
      "December",
    ],
    stats: MatrixStats.NOCOL,
  },
  [HydroMatrixType.Allocation]: {
    title: "Allocation",
    url: "",
    stats: MatrixStats.NOCOL,
    fetchFn: getAllocationMatrix,
    disableEdit: true,
    enablePercentDisplay: true,
  },
  [HydroMatrixType.Correlation]: {
    title: "Correlation",
    url: "",
    stats: MatrixStats.NOCOL,
    fetchFn: getCorrelationMatrix,
    disableEdit: true,
    enablePercentDisplay: true,
  },
};

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

/**
 * Generates an array of column names from 0 to 100, optionally with a suffix.
 * @param columnSuffix The suffix to append to the column names.
 * @returns An array of strings representing column names from 0 to 100.
 */
function generateColumns(columnSuffix = ""): string[] {
  const columns: string[] = [];
  for (let i = 0; i <= 100; i += 1) {
    columns.push(`${i}${columnSuffix}`);
  }
  return columns;
}
