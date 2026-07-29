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
import { isNonEmptyMatrix } from "@/components/Matrix/shared/types";
import { generateCustomColumns, generateDateTime } from "@/components/Matrix/shared/utils";
import EmptyView from "@/components/page/EmptyView";
import UsePromiseCond, { mergeResponses } from "@/components/utils/UsePromiseCond";
import usePromise from "@/hooks/usePromise";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import {
  getOutputMatrixIndex,
  getVariableViewData,
} from "@/services/api/studies/outputs/variableViews";
import GridOffIcon from "@mui/icons-material/GridOff";
// import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import { Button } from "@mui/material";
import { isAxiosError } from "axios";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useUnmount } from "react-use";
import useOutput from "../../-hooks/useOutput";
import useOutputContext from "../../-hooks/useOutputFilters";
import { buildVariableViewParams, DATE_GRID_COLUMN, isClusterDataType } from "./utils";

function OutputVariableMatrix() {
  const { t } = useTranslation();
  const study = useStudy();
  const output = useOutput();
  const { item, dataType, frequency, variable, clusterId, setIsMatrixDataLoaded, matrixGridRef } =
    useOutputContext();

  ////////////////////////////////////////////////////////////////
  // Promises
  ////////////////////////////////////////////////////////////////

  const variableViewDataResponse = usePromise(
    () => {
      if (!variable || (isClusterDataType(dataType) && !clusterId)) {
        return Promise.resolve(undefined);
      }

      return getVariableViewData({
        studyId: study.id,
        outputId: output.id,
        params: buildVariableViewParams({ item, dataType, frequency, clusterId, variable }),
      });
    },
    {
      onDataChange: (data) => {
        setIsMatrixDataLoaded(!!data && isNonEmptyMatrix(data.data));
      },
      resetDataOnReload: true,
      resetErrorOnReload: true,
      deps: [study.id, output.id, dataType, clusterId, item, variable, frequency],
    },
  );

  const matrixIndexResponse = usePromise(
    () => getOutputMatrixIndex({ studyId: study.id, outputId: output.id, frequency }),
    {
      resetDataOnReload: true,
      resetErrorOnReload: true,
      deps: [study.id, output.id, frequency],
    },
  );

  useUnmount(() => {
    setIsMatrixDataLoaded(false);
  });

  ////////////////////////////////////////////////////////////////
  // Columns
  ////////////////////////////////////////////////////////////////

  const gridColumns = useMemo(() => {
    if (!variableViewDataResponse.data || !variableViewDataResponse.data.columns) {
      return [];
    }

    return [
      DATE_GRID_COLUMN,
      ...generateCustomColumns({
        titles: variableViewDataResponse.data.columns.map((col) => `${t("global.year")} ${col}`),
      }),
    ];
  }, [variableViewDataResponse.data, t]);

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
      response={mergeResponses(variableViewDataResponse, matrixIndexResponse)}
      ifPending={() => <DataGridSkeleton />}
      ifFulfilled={([variableViewData, matrixIndex]) => {
        if (!variableViewData || !isNonEmptyMatrix(variableViewData.data)) {
          return <EmptyView title={t("study.outputs.noData")} icon={GridOffIcon} />;
        }

        return (
          <FilterableMatrixGrid
            ref={matrixGridRef}
            data={variableViewData.data}
            rows={variableViewData.data.length}
            columns={gridColumns}
            dateTime={dateTime}
            timeFrequency={matrixIndex.level}
            readOnly
          />
        );
      }}
      ifRejected={(err) => {
        const error = isAxiosError(err) ? err.response?.data : undefined;
        const status = error?.status;
        const taskId = error?.task_id;

        // NOT_FOUND status with no task ID means data not materialized yet
        if (status === "NOT_FOUND" && taskId === null) {
          return (
            <EmptyView
              title={t("study.outputs.scanRequired")}
              icon={GridOffIcon}
              primaryActions={
                <Button
                  variant="contained"
                  color="primary"
                  //   onClick={onMaterializeVariable}
                  //   disabled={isMaterializing}
                  //   startIcon={isMaterializing ? <CircularProgress size={16} /> : <PlayArrowIcon />}
                >
                  {t("study.outputs.process")}
                </Button>
              }
            />
          );
        }

        // Other 404 errors (variable doesn't exist, invalid data, etc.)
        return <EmptyView title={t("data.error.matrix")} icon={GridOffIcon} />;
      }}
    />
  );
}

export default OutputVariableMatrix;
