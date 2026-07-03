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

import DataGridSkeleton from "@/components/DataGridSkeleton";
import FilterableMatrixGrid from "@/components/Matrix/components/FilterableMatrixGrid";
import type { MatrixFilterHandle } from "@/components/Matrix/components/MatrixFilter/types";
import { Column } from "@/components/Matrix/shared/constants";
import { isNonEmptyMatrix, type MatrixResultDTO } from "@/components/Matrix/shared/types";
import {
  generateDateTime,
  generateResultColumns,
  groupResultColumns,
} from "@/components/Matrix/shared/utils";
import EmptyView from "@/components/page/EmptyView";
import ViewWrapper from "@/components/page/ViewWrapper";
import UsePromiseCond, { mergeResponses } from "@/components/utils/UsePromiseCond";
import usePromise from "@/hooks/usePromise";
import useThemeColorScheme from "@/hooks/useThemeColorScheme";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import { getStudyMatrixIndex } from "@/services/api/matrix";
import { getStudyData } from "@/services/api/study";
import type { MatrixIndex } from "@/types/types";
import { sanitizeJsonResponse } from "@/utils/apiUtils";
import { toError } from "@/utils/fnUtils";
import { isSearchMatching } from "@/utils/stringUtils";
import GridOffIcon from "@mui/icons-material/GridOff";
import * as R from "ramda";
import { useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import useOutput from "../../-hooks/useOutput";
import {
  createOutputDataPath,
  type DataType,
  type Frequency,
  type Item,
  type MonteCarloMode,
} from "../../-utils";
import Header from "./Header";
import OutputFiltersContext, { type OutputFiltersContextValue } from "./OutputFiltersContext";
import type { ColumnsInfo } from "./utils";

interface Props {
  selectedItem: Item;
}

function OutputMatrixViewer2({ selectedItem }: Props) {
  const [monteCarloMode, setMonteCarloMode] = useState<MonteCarloMode>("mc-all");
  const [dataType, setDataType] = useState<DataType>("values");
  const [frequency, setFrequency] = useState<Frequency>("hourly");
  const [year, setYear] = useState(-1);
  const [columnsSearch, setColumnsSearch] = useState<ColumnsInfo>({
    variables: [],
    units: [],
    stats: [],
  });
  const study = useStudy();
  const output = useOutput();
  const { t } = useTranslation();
  const { isDarkMode } = useThemeColorScheme();
  const matrixGridRef = useRef<MatrixFilterHandle>(null);

  const outputDataPath = createOutputDataPath({
    output,
    item: selectedItem,
    dataType,
    frequency,
    year,
  });

  const matrixResultResponse = usePromise(
    async () => {
      const data = await getStudyData<MatrixResultDTO | string>(study.id, outputDataPath);
      return sanitizeJsonResponse<MatrixResultDTO>(data);
    },
    {
      resetDataOnReload: true,
      resetErrorOnReload: true,
      deps: [output, selectedItem, dataType, frequency, year, study.id],
    },
  );

  const filteredColumns = useMemo(() => {
    if (!matrixResultResponse.data) {
      return [];
    }

    return matrixResultResponse.data.columns.filter(([variable, unit, stat]) => {
      return (
        (columnsSearch.variables.length === 0 ||
          isSearchMatching(columnsSearch.variables, variable)) &&
        (columnsSearch.units.length === 0 || isSearchMatching(columnsSearch.units, unit)) &&
        (columnsSearch.stats.length === 0 || isSearchMatching(columnsSearch.stats, stat))
      );
    });
  }, [matrixResultResponse.data, columnsSearch]);

  const gridColumns = useMemo(() => {
    if (filteredColumns.length === 0) {
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
        ...generateResultColumns({ titles: filteredColumns }),
      ],
      isDarkMode,
    );
  }, [filteredColumns, isDarkMode]);

  const matrixIndexResponse = usePromise<MatrixIndex | undefined>(
    () => getStudyMatrixIndex(study.id, outputDataPath),
    {
      deps: [study.id, outputDataPath],
    },
  );

  const dateTime = useMemo(
    () => matrixIndexResponse.data && generateDateTime(matrixIndexResponse.data),
    [matrixIndexResponse.data],
  );

  const contextValue = useMemo(() => {
    const columns = matrixResultResponse.data?.columns || [];

    return {
      monteCarloMode,
      setMonteCarloMode,
      year,
      setYear,
      dataType,
      setDataType,
      frequency,
      setFrequency,
      columnsSearch,
      setColumnsSearch,
      columnsData: {
        variables: R.uniq(columns.map((col) => col[0])),
        units: R.uniq(columns.map((col) => col[1])),
        stats: R.uniq(columns.map((col) => col[2].toLowerCase())),
      } satisfies ColumnsInfo,
      matrixGridRef,
    } satisfies OutputFiltersContextValue;
  }, [
    monteCarloMode,
    setMonteCarloMode,
    year,
    setYear,
    dataType,
    setDataType,
    frequency,
    setFrequency,
    columnsSearch,
    setColumnsSearch,
    matrixResultResponse.data,
  ]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ViewWrapper flex={{ gap: 1 }}>
      <OutputFiltersContext value={contextValue}>
        <Header outputDataPath={outputDataPath} />
      </OutputFiltersContext>
      <UsePromiseCond
        response={mergeResponses(matrixResultResponse, matrixIndexResponse)}
        ifPending={() => <DataGridSkeleton />}
        ifFulfilled={([matrixResult, matrixIndex]) => {
          if (!isNonEmptyMatrix(matrixResult.data)) {
            return <EmptyView title={t("study.outputs.noData")} icon={GridOffIcon} />;
          }

          return (
            <FilterableMatrixGrid
              ref={matrixGridRef}
              data={matrixResult.data}
              rows={matrixResult.data.length}
              columns={gridColumns}
              dateTime={dateTime}
              timeFrequency={matrixIndex.level}
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
                ? t("study.outputs.noData")
                : t("data.error.matrix")
            }
            icon={GridOffIcon}
          />
        )}
      />
    </ViewWrapper>
  );
}

export default OutputMatrixViewer2;
