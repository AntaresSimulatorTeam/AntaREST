/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import type {
  MatrixDataDTO,
  AggregateConfig,
  RowCountSource,
} from "../../../../../../common/Matrix/shared/types";
import type { SplitViewProps } from "../../../../../../common/SplitView";
import { getAllocationMatrix } from "./Allocation/utils";
import { getCorrelationMatrix } from "./Correlation/utils";
import InflowStructure from "./InflowStructure";

////////////////////////////////////////////////////////////////
// Enums
////////////////////////////////////////////////////////////////

export const HydroMatrix = {
  Dailypower: "Dailypower",
  EnergyCredits: "EnergyCredits",
  ReservoirLevels: "ReservoirLevels",
  WaterValues: "WaterValues",
  HydroStorage: "HydroStorage",
  RunOfRiver: "RunOfRiver",
  MinGen: "MinGen",
  InflowPattern: "InflowPattern",
  OverallMonthlyHydro: "OverallMonthlyHydro",
  Allocation: "Allocation",
  Correlation: "Correlation",
} as const;

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export type fetchMatrixFn = (studyId: string) => Promise<MatrixDataDTO>;
export type HydroMatrixType = (typeof HydroMatrix)[keyof typeof HydroMatrix];

export interface HydroMatrixProps {
  title: string;
  url: string;
  columns?: string[];
  rowHeaders?: string[];
  fetchFn?: fetchMatrixFn;
  aggregates?: AggregateConfig;
  dateTimeColumn?: boolean;
  readOnly?: boolean;
  showPercent?: boolean;
  rowCountSource?: RowCountSource;
  isTimeSeries?: boolean;
}

type Matrices = Record<HydroMatrixType, HydroMatrixProps>;

export interface HydroRoute {
  path: string;
  type: HydroMatrixType;
  isSplitView?: boolean;
  splitConfig?: {
    direction: SplitViewProps["direction"];
    partnerType: HydroMatrixType;
    sizes: [number, number];
  };
  form?: React.ComponentType;
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
    path: "inflow-structure",
    type: HydroMatrix.InflowPattern,
    isSplitView: true,
    splitConfig: {
      direction: "horizontal",
      partnerType: HydroMatrix.OverallMonthlyHydro,
      sizes: [50, 50],
    },
    form: InflowStructure,
  },
  {
    path: "dailypower&energy",
    type: HydroMatrix.Dailypower,
    isSplitView: true,
    splitConfig: {
      direction: "vertical",
      partnerType: HydroMatrix.EnergyCredits,
      sizes: [30, 70],
    },
  },
  {
    path: "reservoirlevels",
    type: HydroMatrix.ReservoirLevels,
  },
  {
    path: "watervalues",
    type: HydroMatrix.WaterValues,
  },
  {
    path: "hydrostorage",
    type: HydroMatrix.HydroStorage,
  },
  {
    path: "ror",
    type: HydroMatrix.RunOfRiver,
  },
  {
    path: "mingen",
    type: HydroMatrix.MinGen,
  },
];

export const MATRICES: Matrices = {
  [HydroMatrix.Dailypower]: {
    title: "Credit Modulations",
    url: "input/hydro/common/capacity/creditmodulations_{areaId}",
    columns: generateColumns("%"),
    rowHeaders: ["Generating Power", "Pumping Power"],
    rowCountSource: "dataLength",
    dateTimeColumn: false,
    isTimeSeries: false,
  },
  [HydroMatrix.EnergyCredits]: {
    title: "Standard Credits",
    url: "input/hydro/common/capacity/maxpower_{areaId}",
    columns: [
      "Generating Max Power (MW)",
      "Generating Max Energy (Hours at Pmax)",
      "Pumping Max Power (MW)",
      "Pumping Max Energy (Hours at Pmax)",
    ],
    rowCountSource: "dataLength",
    isTimeSeries: false,
  },
  [HydroMatrix.ReservoirLevels]: {
    title: "Reservoir Levels",
    url: "input/hydro/common/capacity/reservoir_{areaId}",
    columns: ["Lev Low (%)", "Lev Avg (%)", "Lev High (%)"],
    isTimeSeries: false,
  },
  [HydroMatrix.WaterValues]: {
    title: "Water Values",
    url: "input/hydro/common/capacity/waterValues_{areaId}",
    // columns: generateColumns("%"), // TODO this causes Runtime error to be fixed
  },
  [HydroMatrix.HydroStorage]: {
    title: "Hydro Storage",
    url: "input/hydro/series/{areaId}/mod",
    aggregates: "stats",
  },
  [HydroMatrix.RunOfRiver]: {
    title: "Run Of River",
    url: "input/hydro/series/{areaId}/ror",
    aggregates: "stats",
  },
  [HydroMatrix.MinGen]: {
    title: "Min Gen",
    url: "input/hydro/series/{areaId}/mingen",
  },
  [HydroMatrix.InflowPattern]: {
    title: "Inflow Pattern",
    url: "input/hydro/common/capacity/inflowPattern_{areaId}",
    columns: ["Inflow Pattern (X)"],
    isTimeSeries: false,
  },
  [HydroMatrix.OverallMonthlyHydro]: {
    title: "Overall Monthly Hydro",
    url: "input/hydro/prepro/{areaId}/energy",
    columns: ["Expectation (MWh)", "Std Deviation (MWh)", "Min. (MWh)", "Max. (MWh)", "ROR Share"],
    rowHeaders: [
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
    rowCountSource: "dataLength",
    dateTimeColumn: false,
    isTimeSeries: false,
  },
  [HydroMatrix.Allocation]: {
    title: "Allocation",
    url: "",
    fetchFn: getAllocationMatrix,
    dateTimeColumn: false,
    readOnly: true,
  },
  [HydroMatrix.Correlation]: {
    title: "Correlation",
    url: "",
    fetchFn: getCorrelationMatrix,
    dateTimeColumn: false,
    readOnly: true,
  },
};

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

/**
 * Generates an array of column names from 0 to 100, optionally with a suffix.
 *
 * @param columnSuffix - The suffix to append to the column names.
 * @returns An array of strings representing column names from 0 to 100.
 */
function generateColumns(columnSuffix = ""): string[] {
  const columns: string[] = [];
  for (let i = 0; i <= 100; i += 1) {
    columns.push(`${i}${columnSuffix}`);
  }
  return columns;
}
