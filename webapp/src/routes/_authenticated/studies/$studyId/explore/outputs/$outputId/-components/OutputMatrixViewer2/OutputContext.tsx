/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import type { MatrixFilterHandle } from "@/components/Matrix/components/MatrixFilter/types";
import { createContext } from "react";
import type { DataType, Frequency, Item, MonteCarloMode } from "../../-utils";
import type { ColumnsInfo } from "./utils";

export interface OutputContextValue {
  item: Item;
  isMatrixDataLoaded: boolean;
  setIsMatrixDataLoaded: React.Dispatch<React.SetStateAction<boolean>>;
  // Result filters
  monteCarloMode: MonteCarloMode;
  setMonteCarloMode: React.Dispatch<React.SetStateAction<MonteCarloMode>>;
  year: number;
  setYear: React.Dispatch<React.SetStateAction<number>>;
  dataType: DataType;
  setDataType: React.Dispatch<React.SetStateAction<DataType>>;
  frequency: Frequency;
  setFrequency: React.Dispatch<React.SetStateAction<Frequency>>;
  variable: string;
  setVariable: React.Dispatch<React.SetStateAction<string>>;
  clusterId: string;
  setClusterId: React.Dispatch<React.SetStateAction<string>>;
  // Columns filters
  columnsSearch: ColumnsInfo;
  setColumnsSearch: React.Dispatch<React.SetStateAction<ColumnsInfo>>;
  columnsData: ColumnsInfo;
  setColumnsData: React.Dispatch<React.SetStateAction<ColumnsInfo>>;
  matrixGridRef: React.RefObject<MatrixFilterHandle | null>;
}

const OutputContext = createContext<OutputContextValue | undefined>(undefined);

export default OutputContext;
