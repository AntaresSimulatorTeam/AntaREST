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

import { type FilterableMatrixGridHandle } from "@/components/Matrix/components/FilterableMatrixGrid";
import type {
  DateTimeMetadataDTO,
  DateTimes,
  EnhancedGridColumn,
  ResultMatrixDTO,
} from "@/components/Matrix/shared/types";
import ViewWrapper from "@/components/page/ViewWrapper";
import type { UsePromiseResponse } from "@/hooks/usePromise";
import type {
  VariablesListDTO,
  VariableViewMatrixDTO,
} from "@/services/api/studies/outputs/variableViews/types";
import type { Area, LinkElement, MatrixIndex } from "@/types/types";
import { Box } from "@mui/material";
import type { PartialStudyOutput } from "../../hooks/useStudyOutput";
import {
  type DataType,
  type Frequency,
  MAX_YEAR,
  type MonteCarloMode,
  type OutputItemType,
} from "../../utils";
import ResultFilters from "../ResultFilters";
import ResultMatrix from "./ResultMatrix";
import VariableMatrix from "./VariableMatrix";

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
  frequency: Frequency;
  setFrequency: (frequency: Frequency) => void;
  output: PartialStudyOutput | undefined;
  studyId: string;
  path: string;
  onColHeadersChange: (headers: string[][], indices: number[]) => void;
  onToggleFilter: () => void;
  variablesMetadata: VariablesListDTO | null;
  itemType: OutputItemType;
  selectedItemId: string;
  selectedItem: (Area & { id: string }) | LinkElement | undefined;
  selectedVariable: string;
  onVariableSelect: (variable: string) => void;
  onMaterializeVariable: () => void;
  isMaterializing: boolean;
  variableViewDataRes: UsePromiseResponse<VariableViewMatrixDTO | null>;
  variableViewColumns: EnhancedGridColumn[];
  variableViewDateTime: DateTimes | undefined;
  variableViewTimeIndexMetadata: DateTimeMetadataDTO | undefined;
  selectedClusterId: string;
  onClusterSelect: (clusterId: string) => void;
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
  frequency,
  setFrequency,
  output,
  studyId,
  path,
  onColHeadersChange,
  onToggleFilter,
  variablesMetadata,
  itemType,
  selectedItemId,
  selectedItem,
  selectedVariable,
  onVariableSelect,
  onMaterializeVariable,
  isMaterializing,
  variableViewDataRes,
  variableViewColumns,
  variableViewDateTime,
  variableViewTimeIndexMetadata,
  selectedClusterId,
  onClusterSelect,
}: ResultMatrixViewerProps) {
  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

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
            frequency={frequency}
            setFrequency={setFrequency}
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
            selectedClusterId={selectedClusterId}
            onClusterSelect={onClusterSelect}
          />
        </Box>
        <Box
          sx={{
            flex: 1,
            minHeight: 0,
            display: "flex",
            flexDirection: "column",
          }}
        >
          {mcMode === "variable-per-variable" ? (
            <VariableMatrix
              variablesMetadata={variablesMetadata}
              itemType={itemType}
              selectedItemId={selectedItemId}
              selectedItem={selectedItem}
              onMaterializeVariable={onMaterializeVariable}
              isMaterializing={isMaterializing}
              variableViewDataRes={variableViewDataRes}
              resultColumns={variableViewColumns}
              matrixGridRef={matrixGridRef}
              dateTime={variableViewDateTime}
              dateTimeMetadata={variableViewTimeIndexMetadata}
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
