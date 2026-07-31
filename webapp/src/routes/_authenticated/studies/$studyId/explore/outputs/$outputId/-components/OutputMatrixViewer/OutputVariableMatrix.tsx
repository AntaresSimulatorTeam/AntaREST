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
  materializeVariableView,
} from "@/services/api/studies/outputs/variableViews";
import GridOffIcon from "@mui/icons-material/GridOff";
// import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import useTasksMonitor from "@/hooks/useTasksMonitor";
import { outputVariablesViewResponseSchema } from "@/services/api/studies/outputs/variableViews/schemas";
import type { TaskEventPayload } from "@/services/webSocket/types";
import { toError } from "@/utils/fnUtils";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import { Button, CircularProgress } from "@mui/material";
import { isAxiosError } from "axios";
import { useMemo, useState } from "react";
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
  const [isMaterializing, setIsMaterializing] = useState(false);
  const [materializeTaskId, setMaterializeTaskId] = useState<string | undefined>(undefined);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  useTasksMonitor({
    taskIds: materializeTaskId,
    onCompleted: handleMaterializeTaskCompleted,
    onFailed: handleMaterializeTaskFailed,
  });

  ////////////////////////////////////////////////////////////////
  // Promises
  ////////////////////////////////////////////////////////////////

  const variableViewDataResponse = usePromise(
    () => {
      if (!variable || (isClusterDataType(dataType) && !clusterId)) {
        // `undefined` is not safely narrowed by `mergeResponses()`
        return Promise.resolve(null);
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
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleMaterialize = async () => {
    setIsMaterializing(true);

    const params = buildVariableViewParams({ dataType, clusterId, item, variable, frequency });

    try {
      const taskId = await materializeVariableView({
        studyId: study.id,
        outputId: output.id,
        params,
      });

      setMaterializeTaskId(taskId);
    } catch (err) {
      setIsMaterializing(false);
      enqueueErrorSnackbar(t("study.outputs.materializationFailed"), toError(err));
      return;
    }
  };

  function handleMaterializeTaskCompleted() {
    setIsMaterializing(false);
    setMaterializeTaskId(undefined);
    variableViewDataResponse.reload();
  }

  function handleMaterializeTaskFailed({ message }: TaskEventPayload) {
    setIsMaterializing(false);
    setMaterializeTaskId(undefined);
    enqueueErrorSnackbar(t("study.outputs.materializationFailed"), toError(message));
  }

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
        const result = isAxiosError(err)
          ? outputVariablesViewResponseSchema.safeParse(err.response?.data)
          : undefined;

        if (result?.success) {
          const { status, taskId } = result.data;
          const isInProgress = status === "IN_PROGRESS" || isMaterializing;

          if (!materializeTaskId && taskId) {
            setMaterializeTaskId(taskId);
          }

          return (
            <EmptyView
              title={t("study.outputs.scanRequired")}
              icon={GridOffIcon}
              primaryActions={
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleMaterialize}
                  disabled={isInProgress}
                  startIcon={isInProgress ? <CircularProgress size={16} /> : <PlayArrowIcon />}
                >
                  {isInProgress ? t("study.outputs.processInProgress") : t("study.outputs.process")}
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
