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
import type { DataType, Frequency, MonteCarloMode } from "../../-utils";
import type { ColumnsInfo } from "./utils";

export interface OutputFiltersContextValue {
  monteCarloMode: MonteCarloMode;
  setMonteCarloMode: React.Dispatch<React.SetStateAction<MonteCarloMode>>;
  year: number;
  setYear: React.Dispatch<React.SetStateAction<number>>;
  dataType: DataType;
  setDataType: React.Dispatch<React.SetStateAction<DataType>>;
  frequency: Frequency;
  setFrequency: React.Dispatch<React.SetStateAction<Frequency>>;
  columnsSearch: ColumnsInfo;
  setColumnsSearch: React.Dispatch<React.SetStateAction<ColumnsInfo>>;
  columnsData: ColumnsInfo;
  matrixGridRef: React.RefObject<MatrixFilterHandle | null>;
}

const OutputFiltersContext = createContext<OutputFiltersContextValue | undefined>(undefined);

export default OutputFiltersContext;
