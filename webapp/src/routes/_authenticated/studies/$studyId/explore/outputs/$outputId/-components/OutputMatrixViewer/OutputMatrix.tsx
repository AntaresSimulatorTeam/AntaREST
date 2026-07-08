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
import { isNonEmptyMatrix, type MatrixResultDTO } from "@/components/Matrix/shared/types";
import {
  generateDateTime,
  generateResultColumns,
  groupResultColumns,
} from "@/components/Matrix/shared/utils";
import EmptyView from "@/components/page/EmptyView";
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
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useUnmount } from "react-use";
import useOutput from "../../-hooks/useOutput";
import useOutputFilters from "../../-hooks/useOutputFilters";
import { createOutputDataPath, DATE_GRID_COLUMN } from "./utils";

function OutputMatrix() {
  const { t } = useTranslation();
  const study = useStudy();
  const output = useOutput();
  const { isDarkMode } = useThemeColorScheme();
  const {
    item,
    dataType,
    frequency,
    year,
    columnsSearch,
    setColumnsData,
    setIsMatrixDataLoaded,
    matrixGridRef,
  } = useOutputFilters();

  const path = createOutputDataPath({
    output,
    item,
    dataType,
    frequency,
    year,
  });

  ////////////////////////////////////////////////////////////////
  // Promises
  ////////////////////////////////////////////////////////////////

  const matrixResultResponse = usePromise(
    async () => {
      const data = await getStudyData<MatrixResultDTO | string>(study.id, path);
      return sanitizeJsonResponse<MatrixResultDTO>(data);
    },
    {
      onDataChange: (data) => {
        const columns = data?.columns || [];

        setColumnsData({
          variables: R.uniq(columns.map((col) => col[0])),
          units: R.uniq(columns.map((col) => col[1])),
          stats: R.uniq(columns.map((col) => col[2].toLowerCase())),
        });

        setIsMatrixDataLoaded(!!data && isNonEmptyMatrix(data.data));
      },
      resetDataOnReload: true,
      resetErrorOnReload: true,
      deps: [study.id, path],
    },
  );

  const matrixIndexResponse = usePromise<MatrixIndex | undefined>(
    () => getStudyMatrixIndex(study.id, path),
    {
      resetDataOnReload: true,
      resetErrorOnReload: true,
      deps: [study.id, path],
    },
  );

  useUnmount(() => {
    setIsMatrixDataLoaded(false);
  });

  ////////////////////////////////////////////////////////////////
  // Columns
  ////////////////////////////////////////////////////////////////

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
      [DATE_GRID_COLUMN, ...generateResultColumns({ titles: filteredColumns })],
      isDarkMode,
    );
  }, [filteredColumns, isDarkMode]);

  ////////////////////////////////////////////////////////////////
  // DateTime
  ////////////////////////////////////////////////////////////////

  const dateTime = useMemo(
    () => matrixIndexResponse.data && generateDateTime(matrixIndexResponse.data),
    [matrixIndexResponse.data],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
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
  );
}

export default OutputMatrix;
