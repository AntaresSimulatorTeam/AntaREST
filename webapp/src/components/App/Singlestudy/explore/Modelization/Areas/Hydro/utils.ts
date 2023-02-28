import { MatrixStats } from "../../../../../../../common/types";

////////////////////////////////////////////////////////////////
// Enums
////////////////////////////////////////////////////////////////

export enum MatrixType {
  Dailypower,
  EnergyCredits,
  ReservoirLevels,
  WaterValues,
  HydroStorage,
  RunOfRiver,
}

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

interface HydroMatrixProps {
  title: string;
  url: string;
  cols?: string[];
  stats: MatrixStats;
}

type Matrices = Record<MatrixType, HydroMatrixProps>;

export interface HydroRoute {
  path: string;
  type: number;
}

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const HYDRO_ROUTES: HydroRoute[] = [
  {
    path: "dailypower",
    type: MatrixType.Dailypower,
  },
  {
    path: "energycredits",
    type: MatrixType.EnergyCredits,
  },
  {
    path: "reservoirlevels",
    type: MatrixType.ReservoirLevels,
  },
  {
    path: "watervalues",
    type: MatrixType.WaterValues,
  },
  {
    path: "hydrostorage",
    type: MatrixType.HydroStorage,
  },
  {
    path: "ror",
    type: MatrixType.RunOfRiver,
  },
];

export const MATRICES: Matrices = {
  [MatrixType.Dailypower]: {
    title: "Daily power",
    url: "input/hydro/common/capacity/creditmodulations_{areaId}",
    cols: generateColumns(),
    stats: MatrixStats.NOCOL,
  },
  [MatrixType.EnergyCredits]: {
    title: "Standard credit",
    url: "input/hydro/common/capacity/maxpower_{areaId}",
    cols: [
      "Generating Max Power(MW)",
      "Generating Max Energy(Hours at Pmax)",
      "Pumping Max Power(MW)",
      "Pumping Max Energy(Hours at Pmax)",
    ],
    stats: MatrixStats.NOCOL,
  },
  [MatrixType.ReservoirLevels]: {
    title: "Reservoir levels",
    url: "input/hydro/common/capacity/reservoir_{areaId}",
    cols: ["Lev Low (p.u)", "Lev Avg (p.u)", "Lev High (p.u)"],
    stats: MatrixStats.NOCOL,
  },
  [MatrixType.WaterValues]: {
    title: "Water values",
    url: "input/hydro/common/capacity/waterValues_{areaId}",
    cols: generateColumns("%"),
    stats: MatrixStats.NOCOL,
  },
  [MatrixType.HydroStorage]: {
    title: "Hydro storage",
    url: "input/hydro/series/{areaId}/mod",
    stats: MatrixStats.STATS,
  },
  [MatrixType.RunOfRiver]: {
    title: "Run of river",
    url: "input/hydro/series/{areaId}/ror",
    stats: MatrixStats.STATS,
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
