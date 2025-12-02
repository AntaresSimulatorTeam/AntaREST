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

import { Box } from "@mui/material";
import type {
  DateTimes,
  EnhancedGridColumn,
  ResultMatrixDTO,
} from "@/components/common/Matrix/shared/types";
import type { UsePromiseResponse } from "@/hooks/usePromise";
import type { MatrixIndex } from "@/types/types";
import type { FilterableMatrixGridHandle } from "../../../../../../common/Matrix/components/FilterableMatrixGrid";
import ViewWrapper from "../../../../../../common/page/ViewWrapper";
import type { PartialStudyOutput } from "../../hooks/useStudyOutput";
import {
  type DataType,
  MAX_YEAR,
  type MonteCarloMode,
  type OutputItemType,
  type Timestep,
} from "../utils";
import ResultFilters from "./ResultFilters";
import ResultMatrix from "./ResultMatrix";
import VariableMatrix from "./VariableMatrix";
import type { VariablesListDTO } from "@/services/api/studies/outputs/variableViews/types";

interface ResultMatrixViewerProps {
  matrixRes: UsePromiseResponse<ResultMatrixDTO | undefined>;
  resultColHeaders: string[][];
  filteredData: number[][];
  resultColumns: EnhancedGridColumn[];
  matrixGridRef: React.RefObject<FilterableMatrixGridHandle>;
  dateTime: DateTimes | undefined;
  dateTimeMetadata: MatrixIndex | undefined;
  mcMode: MonteCarloMode;
  setMcMode: (mode: MonteCarloMode) => void;
  year: number;
  setYear: (year: number) => void;
  dataType: DataType;
  setDataType: (dataType: DataType) => void;
  timestep: Timestep;
  setTimestep: (timestep: Timestep) => void;
  output: PartialStudyOutput | undefined;
  studyId: string;
  path: string;
  onColHeadersChange: (headers: string[][], indices: number[]) => void;
  onToggleFilter: () => void;
  variablesMetadata: VariablesListDTO | null;
  itemType: OutputItemType;
  selectedItemId: string;
  selectedVariable: string;
  onVariableSelect: (variable: string) => void;
  isViewMaterialized: boolean;
  onMaterializeVariable: () => void;
  isMaterializing: boolean;
}

function ResultMatrixViewer({
  matrixRes,
  resultColHeaders,
  filteredData,
  resultColumns,
  matrixGridRef,
  dateTime,
  dateTimeMetadata,
  mcMode,
  setMcMode,
  year,
  setYear,
  dataType,
  setDataType,
  timestep,
  setTimestep,
  output,
  studyId,
  path,
  onColHeadersChange,
  onToggleFilter,
  variablesMetadata,
  itemType,
  selectedItemId,
  selectedVariable,
  onVariableSelect,
  isViewMaterialized,
  onMaterializeVariable,
  isMaterializing,
}: ResultMatrixViewerProps) {
  const isVariablePerVariable = mcMode === "variable-per-variable";

  return (
    <ViewWrapper flex>
      <Box sx={{ display: "flex", flexDirection: "column", height: 1, width: 1 }}>
        <Box sx={{ flexShrink: 0 }}>
          <ResultFilters
            mcMode={mcMode}
            setMcMode={setMcMode}
            year={year}
            setYear={setYear}
            dataType={dataType}
            setDataType={setDataType}
            timestep={timestep}
            setTimestep={setTimestep}
            maxYear={output?.nbyears || MAX_YEAR}
            studyId={studyId}
            path={path}
            colHeaders={matrixRes.data?.columns ?? resultColHeaders}
            onColHeadersChange={onColHeadersChange}
            onToggleFilter={onToggleFilter}
            variablesMetadata={variablesMetadata}
            itemType={itemType}
            selectedItemId={selectedItemId}
            selectedVariable={selectedVariable}
            onVariableSelect={onVariableSelect}
          />
        </Box>
        <Box sx={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
          {isVariablePerVariable ? (
            <VariableMatrix
              variablesMetadata={variablesMetadata}
              mcMode={mcMode}
              itemType={itemType}
              selectedItemId={selectedItemId}
              selectedVariable={selectedVariable}
              isViewMaterialized={isViewMaterialized}
              onMaterializeVariable={onMaterializeVariable}
              isMaterializing={isMaterializing}
              matrixRes={matrixRes}
              resultColHeaders={resultColHeaders}
              filteredData={filteredData}
              resultColumns={resultColumns}
              matrixGridRef={matrixGridRef}
              dateTime={dateTime}
              dateTimeMetadata={dateTimeMetadata}
            />
          ) : (
            <ResultMatrix
              matrixRes={matrixRes}
              resultColHeaders={resultColHeaders}
              filteredData={filteredData}
              resultColumns={resultColumns}
              matrixGridRef={matrixGridRef}
              dateTime={dateTime}
              dateTimeMetadata={dateTimeMetadata}
            />
          )}
        </Box>
      </Box>
    </ViewWrapper>
  );
}

export default ResultMatrixViewer;
