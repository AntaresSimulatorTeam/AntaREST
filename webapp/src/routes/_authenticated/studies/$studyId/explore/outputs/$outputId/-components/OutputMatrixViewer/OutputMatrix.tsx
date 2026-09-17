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
import { isNonEmptyMatrix, type ResultMatrixDTO } from "@/components/Matrix/shared/types";
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
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useUnmount } from "react-use";
import useOutput from "../../-hooks/useOutput";
import useOutputContext from "../../-hooks/useOutputFilters";
import { createOutputDataPath } from "../../-utils";
import { DATE_GRID_COLUMN, isValidColumnStatistic } from "./utils";

function OutputMatrix() {
  const { t } = useTranslation();
  const study = useStudy();
  const output = useOutput();
  const { isDarkMode } = useThemeColorScheme();

  const { item, dataType, frequency, year, columnsFilters, setIsMatrixDataLoaded, matrixGridRef } =
    useOutputContext();

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
      const data = await getStudyData<ResultMatrixDTO | string>(study.id, path);
      return sanitizeJsonResponse<ResultMatrixDTO>(data);
    },
    {
      onDataChange: (data) => {
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

  const gridColumns = useMemo(() => {
    if (!matrixResultResponse.data || matrixResultResponse.data.columns.length === 0) {
      return [];
    }

    return groupResultColumns(
      [DATE_GRID_COLUMN, ...generateResultColumns({ titles: matrixResultResponse.data.columns })],
      isDarkMode,
    );
  }, [matrixResultResponse.data, isDarkMode]);

  const filteredGridColumns = useMemo(() => {
    if (gridColumns.length === 0) {
      return [];
    }

    const hasStatFilter = Object.values(columnsFilters.stats).some((value) => value);

    return gridColumns.map((column) => {
      const { id, group, title } = column;

      if (id === DATE_GRID_COLUMN.id) {
        return column;
      }

      const [variableUnitLabel, statistic] = group ? [group, title] : [title];

      const isVariableUnitLabelMatch =
        columnsFilters.searches.length === 0 ||
        isSearchMatching(columnsFilters.searches, variableUnitLabel);

      const isStatisticMatch =
        !statistic ||
        // Empty stats filter means all stats are included
        !hasStatFilter ||
        (isValidColumnStatistic(statistic) && columnsFilters.stats[statistic]);

      return isVariableUnitLabelMatch && isStatisticMatch
        ? column
        : {
            ...column,
            width: 0, // Hide the column
          };
    });
  }, [columnsFilters, gridColumns]);

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
            columns={filteredGridColumns}
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
