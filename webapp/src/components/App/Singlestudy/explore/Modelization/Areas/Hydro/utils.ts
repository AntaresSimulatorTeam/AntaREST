import { MatrixStats } from "../../../../../../../common/types";

////////////////////////////////////////////////////////////////
// Enums
////////////////////////////////////////////////////////////////

export enum MatrixType {
  Allocation,
  SpatialCorrelation,
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
    path: "allocation",
    type: MatrixType.Allocation,
  },
  {
    path: "spatialcorrelation",
    type: MatrixType.SpatialCorrelation,
  },
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
  [MatrixType.Allocation]: {
    title: "Allocation",
    url: "input/hydro/allocation/{areaId}",
    stats: MatrixStats.NOCOL,
  },
  [MatrixType.SpatialCorrelation]: {
    title: "Spatial correlation",
    url: "input/hydro/allocation/{areaId}",
    stats: MatrixStats.NOCOL,
  },
  [MatrixType.Dailypower]: {
    title: "Daily power",
    url: "input/hydro/common/capacity/creditmodulations_{areaId}",
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
    cols: ["Lev Low(%)", "Lev Avg(%)", "Lev High(%)"],
    stats: MatrixStats.NOCOL,
  },
  [MatrixType.WaterValues]: {
    title: "Water values",
    url: "input/hydro/common/capacity/waterValues_{areaId}",
    stats: MatrixStats.TOTAL,
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
