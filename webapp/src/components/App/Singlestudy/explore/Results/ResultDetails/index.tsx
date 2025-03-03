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

import {
  Box,
  Skeleton,
  ToggleButton,
  ToggleButtonGroup,
  type ToggleButtonGroupProps,
} from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useOutletContext, useParams } from "react-router";
import GridOffIcon from "@mui/icons-material/GridOff";
import type { Area, LinkElement, StudyMetadata } from "../../../../../../types/types";
import usePromise from "../../../../../../hooks/usePromise";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getAreas, getLinks, getStudyOutput } from "../../../../../../redux/selectors";
import { getStudyData } from "../../../../../../services/api/study";
import { isSearchMatching } from "../../../../../../utils/stringUtils";
import PropertiesView from "../../../../../common/PropertiesView";
import ListElement from "../../common/ListElement";
import { createPath, DataType, MAX_YEAR, OutputItemType, SYNTHESIS_ITEMS, Timestep } from "./utils";
import UsePromiseCond, { mergeResponses } from "../../../../../common/utils/UsePromiseCond";
import useStudySynthesis from "../../../../../../redux/hooks/useStudySynthesis";
import ButtonBack from "../../../../../common/ButtonBack";
import MatrixGrid from "../../../../../common/Matrix/components/MatrixGrid/index";
import {
  generateCustomColumns,
  generateDateTime,
  generateResultColumns,
  groupResultColumns,
} from "../../../../../common/Matrix/shared/utils";
import { Column } from "@/components/common/Matrix/shared/constants";
import SplitView from "../../../../../common/SplitView/index";
import ResultFilters from "./ResultFilters";
import { toError } from "../../../../../../utils/fnUtils";
import EmptyView from "../../../../../common/page/EmptyView";
import { getStudyMatrixIndex } from "../../../../../../services/api/matrix";
import type { ResultMatrixDTO } from "@/components/common/Matrix/shared/types";
import DataGridViewer from "@/components/common/DataGridViewer";
import useThemeColorScheme from "@/hooks/useThemeColorScheme";

type SetResultColHeaders = (headers: string[][], indices: number[]) => void;

function ResultDetails() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { isDarkMode } = useThemeColorScheme();
  const { outputId } = useParams();

  const outputRes = useStudySynthesis({
    studyId: study.id,
    selector: (state, id) => getStudyOutput(state, id, outputId as string),
  });

  const { data: output } = outputRes;
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
  const isSynthesis = itemType === OutputItemType.Synthesis;
  const { t } = useTranslation();
  const navigate = useNavigate();

  const items = useAppSelector((state) =>
    itemType === OutputItemType.Areas ? getAreas(state, study.id) : getLinks(state, study.id),
  ) as Array<{ id: string; name: string; label?: string }>;

  const filteredItems = useMemo(() => {
    return isSynthesis
      ? SYNTHESIS_ITEMS
      : items.filter((item) => isSearchMatching(searchValue, item.label || item.name));
  }, [isSynthesis, items, searchValue]);

  const selectedItem = filteredItems.find((item) => item.id === selectedItemId) as
    | (Area & { id: string })
    | LinkElement
    | undefined;

  const maxYear = output?.nbyears ?? MAX_YEAR;

  useEffect(
    () => {
      const isValidSelectedItem =
        !!selectedItemId && filteredItems.find((item) => item.id === selectedItemId);

      if (!isValidSelectedItem) {
        setSelectedItemId(filteredItems.length > 0 ? filteredItems[0].id : "");
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [filteredItems],
  );

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
    if (!matrixRes.data) {
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
      deps: [study.id, outputId, selectedItem],
    },
  );

  const { data: dateTimeMetadata } = usePromise(() => getStudyMatrixIndex(study.id, path), {
    deps: [study.id, path],
  });

  const dateTime = dateTimeMetadata && generateDateTime(dateTimeMetadata);

  const resultColumns = useMemo(() => {
    if (!matrixRes.data) {
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
  }, [matrixRes.data, isDarkMode, resultColHeaders]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleItemTypeChange: ToggleButtonGroupProps["onChange"] = (
    _,
    newValue: OutputItemType,
  ) => {
    if (newValue && newValue !== itemType) {
      setItemType(newValue);
    }
  };

  const handleColHeadersChange: SetResultColHeaders = (headers, indices) => {
    setResultColHeaders(headers);
    setHeaderIndices(indices);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <SplitView id="results" sizes={[15, 85]}>
      {/* Left */}
      <Box>
        <PropertiesView
          topContent={
            <Box sx={{ width: 1, px: 1 }}>
              <ButtonBack onClick={() => navigate("..")} />
            </Box>
          }
          mainContent={
            <>
              <ToggleButtonGroup
                sx={{ p: 1 }}
                value={itemType}
                exclusive
                orientation="vertical"
                fullWidth
                onChange={handleItemTypeChange}
              >
                <ToggleButton value={OutputItemType.Areas}>{t("study.areas")}</ToggleButton>
                <ToggleButton value={OutputItemType.Links}>{t("study.links")}</ToggleButton>
                <ToggleButton value={OutputItemType.Synthesis}>{t("study.synthesis")}</ToggleButton>
              </ToggleButtonGroup>
              <ListElement
                list={filteredItems}
                currentElement={selectedItemId}
                currentElementKeyToTest="id"
                setSelectedItem={(item) => setSelectedItemId(item.id)}
              />
            </>
          }
          onSearchFilterChange={setSearchValue}
        />
      </Box>
      {/* Right */}
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          p: 1,
        }}
      >
        {isSynthesis ? (
          <UsePromiseCond
            response={synthesisRes}
            ifPending={() => <Skeleton sx={{ height: 1, transform: "none" }} />}
            ifFulfilled={(matrix) =>
              matrix && (
                <DataGridViewer
                  data={matrix.data}
                  columns={generateCustomColumns({
                    titles: matrix.columns,
                  })}
                />
              )
            }
          />
        ) : (
          <>
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
            />
            <UsePromiseCond
              response={mergeResponses(outputRes, matrixRes)}
              ifPending={() => <Skeleton sx={{ height: 1, transform: "none" }} />}
              ifFulfilled={([, matrix]) =>
                matrix && (
                  <>
                    {resultColHeaders.length === 0 ? (
                      <EmptyView title={t("study.results.noData")} icon={GridOffIcon} />
                    ) : (
                      <MatrixGrid
                        key={`grid-${resultColHeaders.length}`}
                        data={filteredData}
                        rows={filteredData.length}
                        columns={resultColumns}
                        dateTime={dateTime}
                        readOnly
                      />
                    )}
                  </>
                )
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
          </>
        )}
      </Box>
    </SplitView>
  );
}

export default ResultDetails;
