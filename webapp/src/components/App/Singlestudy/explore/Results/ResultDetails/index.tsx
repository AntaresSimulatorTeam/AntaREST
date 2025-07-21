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

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useOutletContext, useParams } from "react-router";
import type { FilterableMatrixGridHandle } from "@/components/common/Matrix/components/FilterableMatrixGrid";
import { Column } from "@/components/common/Matrix/shared/constants";
import type { ResultMatrixDTO } from "@/components/common/Matrix/shared/types";
import useThemeColorScheme from "@/hooks/useThemeColorScheme";
import type { Area, LinkElement, StudyMetadata } from "@/types/types";
import usePromise from "../../../../../../hooks/usePromise";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getAreas, getLinks } from "../../../../../../redux/selectors";
import { getStudyMatrixIndex } from "../../../../../../services/api/matrix";
import { getStudyData } from "../../../../../../services/api/study";
import { isSearchMatching } from "../../../../../../utils/stringUtils";
import {
  generateDateTime,
  generateResultColumns,
  groupResultColumns,
} from "../../../../../common/Matrix/shared/utils";
import SplitView from "../../../../../common/SplitView/index";
import useStudyOutput from "../hooks/useStudyOutput";
import ResultItemSelector from "./components/ResultItemSelector";
import ResultMatrixViewer from "./components/ResultMatrixViewer";
import SynthesisViewer, { type SynthesisData } from "./components/SynthesisViewer";
import { createPath, DataType, OutputItemType, SYNTHESIS_ITEMS, Timestep } from "./utils";

type SetResultColHeaders = (headers: string[][], indices: number[]) => void;

function ResultDetails() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { isDarkMode } = useThemeColorScheme();
  const { outputId } = useParams();
  const navigate = useNavigate();

  const [dataType, setDataType] = useState(DataType.General);
  const [timestep, setTimestep] = useState(Timestep.Hourly);
  const [year, setYear] = useState(-1);
  const [itemType, setItemType] = useState(OutputItemType.Areas);
  const [selectedItemId, setSelectedItemId] = useState("");
  const [searchValue, setSearchValue] = useState("");
  // Store filtered headers and their original indices separately
  // This allows us to correctly map the data rows to their corresponding headers
  // when some columns are filtered out
  const [resultColHeaders, setResultColHeaders] = useState<string[][]>([]);
  const [headerIndices, setHeaderIndices] = useState<number[]>([]);

  // Ref for the FilterableMatrixGrid to control the filter
  const matrixGridRef = useRef<FilterableMatrixGridHandle>(null);
  const isSynthesis = itemType === OutputItemType.Synthesis;
  const areas = useAppSelector((state) => getAreas(state, study.id));
  const links = useAppSelector((state) => getLinks(state, study.id));

  const { data: output } = useStudyOutput({
    studyId: study.id,
    outputId: outputId,
  });

  const items = useMemo(() => {
    const currentItems = (itemType === OutputItemType.Areas ? areas : links) as Array<{
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

  // Auto-select first item if none selected
  useEffect(() => {
    if (!selectedItem && filteredItems.length > 0) {
      setSelectedItemId(filteredItems[0].id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filteredItems.length, selectedItem]); // Using length to avoid reference issues

  const path = useMemo(() => {
    if (output && selectedItem && !isSynthesis) {
      return createPath({
        output,
        item: selectedItem,
        dataType,
        timestep,
        year,
      });
    }
    return "";
  }, [output, selectedItem, isSynthesis, dataType, timestep, year]);

  const matrixRes = usePromise<ResultMatrixDTO | undefined>(
    async () => {
      if (!output || !selectedItem || isSynthesis || !path) {
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
      deps: [study.id, path, !!output, !!selectedItem, isSynthesis],
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

  const { data: dateTimeMetadata } = usePromise(() => getStudyMatrixIndex(study.id, path), {
    deps: [study.id, path],
  });

  const dateTime = useMemo(
    () => dateTimeMetadata && generateDateTime(dateTimeMetadata),
    [dateTimeMetadata],
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

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <SplitView id="results" sizes={[15, 85]} minSize={[200, 300]}>
      <ResultItemSelector
        itemType={itemType}
        onItemTypeChange={handleItemTypeChange}
        output={output}
        filteredItems={filteredItems}
        selectedItemId={selectedItemId}
        onSetSelectedItemId={handleSetSelectedItemId}
        onSearchChange={handleSearchChange}
        onNavigateBack={() => navigate("..")}
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
          year={year}
          setYear={setYear}
          dataType={dataType}
          setDataType={setDataType}
          timestep={timestep}
          setTimestep={setTimestep}
          output={output}
          studyId={study.id}
          path={path}
          onColHeadersChange={handleColHeadersChange}
          onToggleFilter={handleToggleFilter}
        />
      )}
    </SplitView>
  );
}

export default ResultDetails;
