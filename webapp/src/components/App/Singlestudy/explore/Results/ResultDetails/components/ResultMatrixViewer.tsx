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

import React from "react";
import ResultFilters from "./ResultFilters";
import { useTranslation } from "react-i18next";
import { Box, Skeleton } from "@mui/material";
import GridOffIcon from "@mui/icons-material/GridOff";
import ViewWrapper from "../../../../../../common/page/ViewWrapper";
import EmptyView from "../../../../../../common/page/EmptyView";
import UsePromiseCond from "../../../../../../common/utils/UsePromiseCond";
import FilterableMatrixGrid, {
  type FilterableMatrixGridHandle,
} from "../../../../../../common/Matrix/components/FilterableMatrixGrid";
import { isNonEmptyMatrix } from "../../../../../../common/Matrix/shared/types";
import { toError } from "../../../../../../../utils/fnUtils";
import { DataType, MAX_YEAR, Timestep } from "../utils";

import type { EnhancedGridColumn, ResultMatrixDTO } from "@/components/common/Matrix/shared/types";
import type { UsePromiseResponse } from "@/hooks/usePromise";
import type { MatrixIndex } from "@/types/types";
import type { PartialStudyOutput } from "../../hooks/useStudyOutput";

interface ResultMatrixViewerProps {
  matrixRes: UsePromiseResponse<ResultMatrixDTO | undefined>;
  resultColHeaders: string[][];
  filteredData: number[][];
  resultColumns: EnhancedGridColumn[];
  matrixGridRef: React.RefObject<FilterableMatrixGridHandle>;
  dateTime: string[] | undefined;
  dateTimeMetadata: MatrixIndex | undefined;
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
}

function ResultMatrixViewer({
  matrixRes,
  resultColHeaders,
  filteredData,
  resultColumns,
  matrixGridRef,
  dateTime,
  dateTimeMetadata,
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
}: ResultMatrixViewerProps) {
  const { t } = useTranslation();

  return (
    <ViewWrapper flex>
      <Box sx={{ display: "flex", flexDirection: "column", height: 1, width: 1 }}>
        <Box sx={{ flexShrink: 0 }}>
          <ResultFilters
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
          />
        </Box>
        <Box sx={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
          <UsePromiseCond
            response={matrixRes}
            ifPending={() => <Skeleton sx={{ height: 1, transform: "none" }} />}
            ifFulfilled={() => {
              // If headers haven't been processed yet, show loading
              if (resultColHeaders.length === 0) {
                return <Skeleton sx={{ height: 1, transform: "none" }} />;
              }

              // If we have processed headers but no valid data, show "No data"
              if (!isNonEmptyMatrix(filteredData)) {
                return <EmptyView title={t("study.results.noData")} icon={GridOffIcon} />;
              }

              return (
                <FilterableMatrixGrid
                  ref={matrixGridRef}
                  key={`grid-${resultColHeaders.length}`}
                  data={filteredData}
                  rows={filteredData.length}
                  columns={resultColumns}
                  dateTime={dateTime}
                  timeFrequency={dateTimeMetadata?.level}
                  readOnly
                />
              );
            }}
            ifRejected={(err) => (
              <EmptyView
                title={
                  // 404 error is expected when their is no data
                  // for the selected area or link result
                  // TODO: Instead this should be an empty response from the server
                  toError(err).message.includes("404")
                    ? t("study.results.noData")
                    : t("data.error.matrix")
                }
                icon={GridOffIcon}
              />
            )}
          />
        </Box>
      </Box>
    </ViewWrapper>
  );
}

export default ResultMatrixViewer;
