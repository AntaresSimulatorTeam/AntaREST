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

import DataGridViewer from "@/components/common/DataGridViewer";
import { Column } from "@/components/common/Matrix/shared/constants";
import { isNonEmptyMatrix, type ResultMatrixDTO } from "@/components/common/Matrix/shared/types";
import ViewWrapper from "@/components/common/page/ViewWrapper";
import useThemeColorScheme from "@/hooks/useThemeColorScheme";
import GridOffIcon from "@mui/icons-material/GridOff";
import { Box, Skeleton, Tab, Tabs } from "@mui/material";
import { useCallback, useEffect, useMemo, useState, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useOutletContext, useParams } from "react-router";
import usePromise from "../../../../../../hooks/usePromise";
import useStudyOutput from "../hooks/useStudyOutput";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getAreas, getLinks } from "../../../../../../redux/selectors";
import { getStudyMatrixIndex } from "../../../../../../services/api/matrix";
import { getStudyData } from "../../../../../../services/api/study";
import { type Area, type LinkElement, type StudyMetadata } from "../../../../../../types/types";
import { toError } from "../../../../../../utils/fnUtils";
import { isSearchMatching } from "../../../../../../utils/stringUtils";
import ButtonBack from "../../../../../common/ButtonBack";
import FilterableMatrixGrid, {
  type FilterableMatrixGridHandle,
} from "../../../../../common/Matrix/components/FilterableMatrixGrid";
import {
  generateCustomColumns,
  generateDateTime,
  generateResultColumns,
  groupResultColumns,
} from "../../../../../common/Matrix/shared/utils";
import EmptyView from "../../../../../common/page/EmptyView";
import PropertiesView from "../../../../../common/PropertiesView";
import SplitView from "../../../../../common/SplitView/index";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";
import ListElement from "../../common/ListElement";
import ResultFilters from "./ResultFilters";
import { createPath, DataType, MAX_YEAR, OutputItemType, SYNTHESIS_ITEMS, Timestep } from "./utils";

type SetResultColHeaders = (headers: string[][], indices: number[]) => void;

function ResultDetails() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { isDarkMode } = useThemeColorScheme();
  const { outputId } = useParams();
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [dataType, setDataType] = useState(DataType.General);
  const [timestep, setTimestep] = useState(Timestep.Hourly);
  const [year, setYear] = useState(-1);
  const [itemType, setItemType] = useState(OutputItemType.Areas);
  const [selectedItemId, setSelectedItemId] = useState("");
  const [searchValue, setSearchValue] = useState("");
  const [resultColHeaders, setResultColHeaders] = useState<string[][]>([]);
  const [headerIndices, setHeaderIndices] = useState<number[]>([]);

  // Ref for the FilterableMatrixGrid to control the filter
  const matrixGridRef = useRef<FilterableMatrixGridHandle>(null);

  const isSynthesis = itemType === OutputItemType.Synthesis;

  const { data: output } = useStudyOutput({
    studyId: study.id,
    outputId: outputId,
  });

  const maxYear = output?.nbyears || MAX_YEAR;

  // Get areas and links from Redux store
  const items = useAppSelector((state) =>
    itemType === OutputItemType.Areas ? getAreas(state, study.id) : getLinks(state, study.id),
  ) as Array<{ id: string; name: string; label?: string }>;

  const filteredItems = useMemo(() => {
    if (isSynthesis) {
      return SYNTHESIS_ITEMS;
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
  }, [filteredItems, selectedItem]);

  // Build fetch path for matrix data
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
      if (!path) {
        return undefined;
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
      deps: [study.id, path],
    },
  );

  // Transform the matrix data by keeping only the columns that match our filters
  // headerIndices contains the original positions of our kept columns, ensuring
  // the data stays aligned with its corresponding headers
  const filteredData = useMemo(() => {
    if (!matrixRes.data?.data) {
      return [];
    }

    return matrixRes.data.data.map((row) => {
      return headerIndices.map((index) => row[index]);
    });
  }, [matrixRes.data, headerIndices]);

  const synthesisRes = usePromise(
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

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <SplitView id="results" sizes={[15, 85]} minSize={[200, 300]}>
      {/* Left Panel - areas list */}
      <Box>
        <PropertiesView
          topContent={
            <Box sx={{ width: 1, px: 1 }}>
              <ButtonBack onClick={() => navigate("..")} />
            </Box>
          }
          mainContent={
            <>
              <Tabs
                value={itemType}
                onChange={handleItemTypeChange}
                size="extra-small"
                variant="fullWidth"
              >
                <Tab label={t("study.areas")} value={OutputItemType.Areas} />
                <Tab label={t("study.links")} value={OutputItemType.Links} />
                {output?.synthesis && (
                  <Tab label={t("study.synthesis")} value={OutputItemType.Synthesis} />
                )}
              </Tabs>
              <ListElement
                list={filteredItems}
                currentElement={selectedItemId}
                currentElementKeyToTest="id"
                setSelectedItem={handleSetSelectedItemId}
              />
            </>
          }
          onSearchFilterChange={setSearchValue}
        />
      </Box>

      {/* Right Panel - results grid */}
      <ViewWrapper flex>
        {isSynthesis ? (
          <UsePromiseCond
            response={synthesisRes}
            ifPending={() => <Skeleton sx={{ height: 1, transform: "none" }} />}
            ifFulfilled={(matrix) => {
              if (!matrix) {
                return <EmptyView title={t("study.results.noData")} icon={GridOffIcon} />;
              }

              return (
                <DataGridViewer
                  data={matrix.data}
                  columns={generateCustomColumns({
                    titles: matrix.columns,
                  })}
                />
              );
            }}
          />
        ) : (
          <Box sx={{ display: "flex", flexDirection: "column", height: 1, width: 1 }}>
            <Box sx={{ flexShrink: 0 }}>
              <ResultFilters
                year={year}
                setYear={setYear}
                dataType={dataType}
                setDataType={setDataType}
                timestep={timestep}
                setTimestep={setTimestep}
                maxYear={maxYear}
                studyId={study.id}
                path={path}
                colHeaders={matrixRes.data?.columns || []}
                onColHeadersChange={handleColHeadersChange}
                onToggleFilter={handleToggleFilter}
              />
            </Box>
            <Box sx={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
              <UsePromiseCond
                response={matrixRes}
                ifPending={() => <Skeleton sx={{ height: 1, transform: "none" }} />}
                ifFulfilled={(matrix) =>
                  matrix &&
                  (resultColHeaders.length === 0 ? (
                    <EmptyView title={t("study.results.noData")} icon={GridOffIcon} />
                  ) : (
                    isNonEmptyMatrix(filteredData) && (
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
                    )
                  ))
                }
                ifRejected={(err) => (
                  <EmptyView
                    title={
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
        )}
      </ViewWrapper>
    </SplitView>
  );
}

export default ResultDetails;
