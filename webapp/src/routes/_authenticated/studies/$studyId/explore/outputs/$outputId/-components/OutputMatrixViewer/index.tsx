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

import type { FilterableMatrixGridHandle } from "@/components/Matrix/components/FilterableMatrixGrid";
import { Column } from "@/components/Matrix/shared/constants";
import type { ResultMatrixDTO } from "@/components/Matrix/shared/types";
import {
  generateCustomColumns,
  generateDateTime,
  generateResultColumns,
  groupResultColumns,
} from "@/components/Matrix/shared/utils";
import ViewWrapper from "@/components/page/ViewWrapper";
import usePromise from "@/hooks/usePromise";
import useThemeColorScheme from "@/hooks/useThemeColorScheme";
import type { StudyMapDistrict } from "@/redux/ducks/studyMaps";
import { getStudyMatrixIndex } from "@/services/api/matrix";
import { getStudyData } from "@/services/api/study";
import type { AreaWithId, LinkElement, MatrixIndex } from "@/types/types";
import { Box } from "@mui/material";
import { useParams } from "@tanstack/react-router";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { PartialStudyOutput } from "../../-hooks/useStudyOutput";
import { useVariablePerVariable } from "../../-hooks/useVariablePerVariable";
import {
  createPath,
  MAX_YEAR,
  type DataType,
  type Frequency,
  type ListType,
  type MonteCarloMode,
} from "../../-utils";
import OutputMatrix from "./OutputMatrix";
import ResultFilters from "./ResultFilters";
import VariableMatrix from "./VariableMatrix";

interface ResultMatrixViewerProps {
  itemType: ListType;
  selectedItem: AreaWithId | StudyMapDistrict | LinkElement;
  output?: PartialStudyOutput;
}

type SetResultColHeaders = (headers: string[][], indices: number[]) => void;

function ResultMatrixViewer({ itemType, selectedItem, output }: ResultMatrixViewerProps) {
  const { studyId, outputId } = useParams({
    from: "/_authenticated/studies/$studyId/explore/outputs/$outputId/",
  });
  const { isDarkMode } = useThemeColorScheme();
  const { t } = useTranslation();
  const [mcMode, setMcMode] = useState<MonteCarloMode>("mc-all");
  const [dataType, setDataType] = useState<DataType>("values");
  const [frequency, setFrequency] = useState<Frequency>("hourly");
  const [year, setYear] = useState(-1);
  const [selectedClusterId, setSelectedClusterId] = useState("");
  const [resultColHeaders, setResultColHeaders] = useState<string[][]>([]);
  const [headerIndices, setHeaderIndices] = useState<number[]>([]);
  const matrixGridRef = useRef<FilterableMatrixGridHandle>(null);

  const isSynthesis = itemType === "synthesis";
  const isVariablePerVariable = mcMode === "variable-per-variable";

  const {
    variablesMetadata,
    timeIndexMetadata,
    selectedVariable,
    setSelectedVariable,
    isMaterializing,
    handleMaterializeVariable,
    variableViewDataRes,
  } = useVariablePerVariable({
    studyId,
    outputId,
    isEnabled: isVariablePerVariable,
    itemType,
    frequency,
    selectedItem,
    dataType,
    selectedClusterId,
  });

  const path = useMemo(() => {
    if (output && selectedItem && !isSynthesis) {
      return createPath({
        output,
        item: selectedItem,
        dataType,
        frequency,
        year,
      });
    }
    return "";
  }, [output, selectedItem, isSynthesis, dataType, frequency, year]);

  const matrixRes = usePromise<ResultMatrixDTO | undefined>(
    async () => {
      if (!output || !selectedItem || isSynthesis || !path || isVariablePerVariable) {
        return new Promise(() => {
          // Intentionally never resolves to keep promise in pending state
          // Prevents invalid "No data" while loading
        });
      }

      const res = await getStudyData(studyId, path);

      // Handle string response (may contain NaN/Infinity)
      // TODO: This should be handled at the API level
      if (typeof res === "string") {
        const fixed = res.replace(/NaN/g, '"NaN"').replace(/Infinity/g, '"Infinity"');
        const parsed = JSON.parse(fixed);

        return {
          ...parsed,
          indices: Array.from({ length: parsed.columns.length }, (_, i) => i),
        };
      }

      return {
        ...res,
        indices: Array.from({ length: res.columns.length }, (_, i) => i),
      };
    },
    {
      resetDataOnReload: true,
      resetErrorOnReload: true,
      deps: [studyId, path, !!output, !!selectedItem, isSynthesis, isVariablePerVariable],
    },
  );

  // Transform the matrix data by keeping only the columns that match our filters
  // headerIndices contains the original positions of our kept columns, ensuring
  // the data stays aligned with its corresponding headers
  const filteredData = useMemo(() => {
    if (!matrixRes.data?.data) {
      return [];
    }

    return matrixRes.data.data.map((row) => headerIndices.map((index) => row[index]));
  }, [matrixRes.data, headerIndices]);

  const { data: dateTimeMetadata } = usePromise<MatrixIndex | undefined>(
    () => {
      // Skip fetching in variable-per-variable mode
      if (isVariablePerVariable || !path) {
        return Promise.resolve(undefined);
      }

      return getStudyMatrixIndex(studyId, path);
    },
    {
      deps: [studyId, path, isVariablePerVariable],
    },
  );

  const dateTime = useMemo(
    () => dateTimeMetadata && generateDateTime(dateTimeMetadata),
    [dateTimeMetadata],
  );

  useEffect(() => {
    if (mcMode === "mc-all") {
      setYear(-1);
    } else if (mcMode === "mc-ind" && year <= 0) {
      setYear(1);
    }
  }, [mcMode, year]);

  // Reset variable and cluster selections when dataType changes in variable-per-variable mode
  useEffect(() => {
    if (isVariablePerVariable) {
      setSelectedVariable("");
      setSelectedClusterId("");
    }
  }, [dataType, isVariablePerVariable, setSelectedVariable]);

  const variableViewDateTime = useMemo(
    () => timeIndexMetadata && generateDateTime(timeIndexMetadata),
    [timeIndexMetadata],
  );

  const resultColumns = useMemo(() => {
    if (!matrixRes.data || resultColHeaders.length === 0) {
      return [];
    }

    return groupResultColumns(
      [
        {
          id: "date",
          title: "Date",
          type: Column.DateTime,
          editable: false,
        },
        ...generateResultColumns({ titles: resultColHeaders }),
      ],
      isDarkMode,
    );
  }, [matrixRes.data, resultColHeaders, isDarkMode]);

  const variableViewColumns = useMemo(() => {
    if (!variableViewDataRes.data || !variableViewDataRes.data.columns) {
      return [];
    }

    return [
      {
        id: "date",
        title: "Date",
        type: Column.DateTime,
        editable: false,
      },
      ...generateCustomColumns({
        titles: variableViewDataRes.data.columns.map((col) => `${t("global.year")} ${col}`),
      }),
    ];
  }, [variableViewDataRes.data, t]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleColHeadersChange = useCallback<SetResultColHeaders>((headers, indices) => {
    setResultColHeaders(headers);
    setHeaderIndices(indices);
  }, []);

  const handleToggleFilter = useCallback(() => {
    matrixGridRef.current?.toggleFilter();
  }, []);

  const handleClusterSelect = (clusterId: string) => {
    setSelectedClusterId(clusterId);
  };

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
            outputId={outputId}
            path={path}
            colHeaders={matrixRes.data?.columns ?? resultColHeaders}
            onColHeadersChange={handleColHeadersChange}
            onToggleFilter={handleToggleFilter}
            variablesMetadata={variablesMetadata ?? null}
            itemType={itemType}
            selectedItem={selectedItem}
            selectedVariable={selectedVariable}
            onVariableSelect={setSelectedVariable}
            selectedClusterId={selectedClusterId}
            onClusterSelect={handleClusterSelect}
            canExportVariableView={
              variableViewDataRes.status === "fulfilled" && !!variableViewDataRes.data
            }
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
              variablesMetadata={variablesMetadata ?? null}
              itemType={itemType}
              selectedItem={selectedItem}
              onMaterializeVariable={handleMaterializeVariable}
              isMaterializing={isMaterializing}
              variableViewDataRes={variableViewDataRes}
              resultColumns={variableViewColumns}
              matrixGridRef={matrixGridRef}
              dateTime={variableViewDateTime}
              dateTimeMetadata={timeIndexMetadata}
            />
          ) : (
            <OutputMatrix
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
