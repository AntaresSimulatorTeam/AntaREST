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

import type { FilterableMatrixGridHandle } from "@/components/Matrix/components/FilterableMatrixGrid";
import { Column } from "@/components/Matrix/shared/constants";
import type { ResultMatrixDTO } from "@/components/Matrix/shared/types";
import {
  generateCustomColumns,
  generateDateTime,
  generateResultColumns,
  groupResultColumns,
} from "@/components/Matrix/shared/utils";
import SplitView from "@/components/page/SplitView/index";
import useThemeColorScheme from "@/hooks/useThemeColorScheme";
import type { Area, LinkElement, MatrixIndex } from "@/types/types";
import { createFileRoute } from "@tanstack/react-router";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import useStudy from "../../../../../../-shared/hook/useStudy";
import usePromise from "../../../../../../../hooks/usePromise";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getAreas, getLinks } from "../../../../../../../redux/selectors";
import { getStudyMatrixIndex } from "../../../../../../../services/api/matrix";
import { getStudyData } from "../../../../../../../services/api/study";
import { isSearchMatching } from "../../../../../../../utils/stringUtils";
import ResultItemSelector from "./-components/ResultItemSelector";
import ResultMatrixViewer from "./-components/ResultMatrixViewer";
import SynthesisViewer, { type SynthesisData } from "./-components/SynthesisViewer";
import useStudyOutput from "./-hooks/useStudyOutput";
import { useVariablePerVariable } from "./-hooks/useVariablePerVariable";
import {
  createPath,
  SYNTHESIS_ITEMS,
  type DataType,
  type Frequency,
  type MonteCarloMode,
  type OutputItemType,
} from "./-utils";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore/outputs/$outputId/")(
  {
    component: Output,
  },
);

type SetResultColHeaders = (headers: string[][], indices: number[]) => void;

function Output() {
  const study = useStudy();
  const { t } = useTranslation();
  const { isDarkMode } = useThemeColorScheme();
  const { outputId } = Route.useParams();
  const navigate = Route.useNavigate();

  const [mcMode, setMcMode] = useState<MonteCarloMode>("mc-all");
  const [dataType, setDataType] = useState<DataType>("values");
  const [frequency, setFrequency] = useState<Frequency>("hourly");
  const [year, setYear] = useState(-1);
  const [itemType, setItemType] = useState<OutputItemType>("areas");
  const [selectedItemId, setSelectedItemId] = useState("");
  const [selectedClusterId, setSelectedClusterId] = useState("");
  const [searchValue, setSearchValue] = useState("");
  const [resultColHeaders, setResultColHeaders] = useState<string[][]>([]);
  const [headerIndices, setHeaderIndices] = useState<number[]>([]);

  const matrixGridRef = useRef<FilterableMatrixGridHandle>(null);
  const isSynthesis = itemType === "synthesis";
  const isVariablePerVariable = mcMode === "variable-per-variable";
  const areas = useAppSelector((state) => getAreas(state, study.id));
  const links = useAppSelector((state) => getLinks(state, study.id));

  const { data: output } = useStudyOutput({
    studyId: study.id,
    outputId: outputId,
  });

  useEffect(() => {
    if (mcMode === "mc-all") {
      setYear(-1);
    } else if (mcMode === "mc-ind" && year <= 0) {
      setYear(1);
    }
  }, [mcMode, year]);

  const items = useMemo(() => {
    const currentItems = (itemType === "areas" ? areas : links) as Array<{
      id: string;
      name: string;
      label?: string;
    }>;

    return Array.isArray(currentItems) ? currentItems : [];
  }, [itemType, areas, links]);

  const filteredItems = useMemo(() => {
    if (isSynthesis) {
      return SYNTHESIS_ITEMS;
    }

    if (!searchValue.trim()) {
      return items;
    }

    return items.filter((item) => isSearchMatching(searchValue, item.label || item.name));
  }, [isSynthesis, items, searchValue]);

  const selectedItem = filteredItems.find((item) => item.id === selectedItemId) as
    | (Area & { id: string })
    | LinkElement
    | undefined;

  const {
    variablesMetadata,
    timeIndexMetadata,
    selectedVariable,
    setSelectedVariable,
    isMaterializing,
    handleMaterializeVariable,
    variableViewDataRes,
  } = useVariablePerVariable({
    studyId: study.id,
    outputId,
    isEnabled: isVariablePerVariable,
    itemType,
    frequency,
    selectedItemId,
    selectedItem,
    dataType,
    selectedClusterId,
  });

  // Reset variable and cluster selections when dataType changes in variable-per-variable mode
  useEffect(() => {
    if (isVariablePerVariable) {
      setSelectedVariable("");
      setSelectedClusterId("");
    }
  }, [dataType, isVariablePerVariable, setSelectedVariable]);

  // Auto-select first item if none selected
  // biome-ignore lint/correctness/useExhaustiveDependencies: <Using length to avoid reference issues>
  useEffect(() => {
    if (!selectedItem && filteredItems.length > 0) {
      setSelectedItemId(filteredItems[0].id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filteredItems.length, selectedItem]);

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

      const res = await getStudyData(study.id, path);

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
      deps: [study.id, path, !!output, !!selectedItem, isSynthesis, isVariablePerVariable],
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

  const synthesisRes = usePromise<SynthesisData | null>(
    () => {
      if (outputId && selectedItem && isSynthesis) {
        const path = `output/${outputId}/economy/mc-all/grid/${selectedItem.id}`;
        return getStudyData(study.id, path);
      }

      return Promise.resolve(null);
    },
    {
      deps: [study.id, outputId, selectedItem, isSynthesis],
    },
  );

  const { data: dateTimeMetadata } = usePromise<MatrixIndex | undefined>(
    () => {
      // Skip fetching in variable-per-variable mode
      if (isVariablePerVariable || !path) {
        return Promise.resolve(undefined);
      }

      return getStudyMatrixIndex(study.id, path);
    },
    {
      deps: [study.id, path, isVariablePerVariable],
    },
  );

  const dateTime = useMemo(
    () => dateTimeMetadata && generateDateTime(dateTimeMetadata),
    [dateTimeMetadata],
  );

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

  const handleItemTypeChange = useCallback(
    (_event: React.SyntheticEvent, newValue: OutputItemType) => {
      if (newValue && newValue !== itemType) {
        setItemType(newValue);
      }
    },
    [itemType],
  );

  const handleColHeadersChange = useCallback<SetResultColHeaders>((headers, indices) => {
    setResultColHeaders(headers);
    setHeaderIndices(indices);
  }, []);

  const handleSetSelectedItemId = useCallback((item: { id: string }) => {
    setSelectedItemId(item.id);
  }, []);

  const handleToggleFilter = useCallback(() => {
    matrixGridRef.current?.toggleFilter();
  }, []);

  const handleSearchChange = useCallback(
    (value: string) => {
      if (value !== searchValue) {
        setSearchValue(value);
      }
    },
    [searchValue],
  );

  const handleClusterSelect = (clusterId: string) => {
    setSelectedClusterId(clusterId);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <SplitView splitId="results" minSize={[150, 400]}>
      <ResultItemSelector
        itemType={itemType}
        onItemTypeChange={handleItemTypeChange}
        output={output}
        filteredItems={filteredItems}
        selectedItemId={selectedItemId}
        onSetSelectedItemId={handleSetSelectedItemId}
        onSearchChange={handleSearchChange}
        onNavigateBack={() => navigate({ to: ".." })}
      />

      {isSynthesis ? (
        <SynthesisViewer synthesisRes={synthesisRes} />
      ) : (
        <ResultMatrixViewer
          matrixRes={matrixRes}
          resultColHeaders={resultColHeaders}
          filteredData={filteredData}
          resultColumns={resultColumns}
          matrixGridRef={matrixGridRef}
          dateTime={dateTime}
          dateTimeMetadata={dateTimeMetadata}
          mcMode={mcMode}
          setMcMode={setMcMode}
          year={year}
          setYear={setYear}
          dataType={dataType}
          setDataType={setDataType}
          frequency={frequency}
          setFrequency={setFrequency}
          output={output}
          studyId={study.id}
          path={path}
          onColHeadersChange={handleColHeadersChange}
          onToggleFilter={handleToggleFilter}
          variablesMetadata={variablesMetadata ?? null}
          itemType={itemType}
          selectedItemId={selectedItemId}
          selectedItem={selectedItem}
          selectedVariable={selectedVariable}
          onVariableSelect={setSelectedVariable}
          onMaterializeVariable={handleMaterializeVariable}
          isMaterializing={isMaterializing}
          variableViewDataRes={variableViewDataRes}
          variableViewColumns={variableViewColumns}
          variableViewDateTime={variableViewDateTime}
          variableViewTimeIndexMetadata={timeIndexMetadata}
          selectedClusterId={selectedClusterId}
          onClusterSelect={handleClusterSelect}
        />
      )}
    </SplitView>
  );
}
