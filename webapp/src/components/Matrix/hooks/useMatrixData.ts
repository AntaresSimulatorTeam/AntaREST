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

import { TimeFrequency } from "@/components/Matrix/shared/constants";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import type { fetchMatrixFn } from "@/routes/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/Hydro/utils";
import { getStudyMatrixIndex } from "@/services/api/matrix";
import { getStudyData } from "@/services/api/study";
import type { MatrixIndex } from "@/types/types";
import { toError } from "@/utils/fnUtils";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import useUndo from "use-undo";
import type {
  AggregateType,
  MatrixAggregates,
  MatrixDataDTO,
  RowCountSource,
} from "../shared/types";
import { calculateMatrixAggregates, generateDateTime } from "../shared/utils";

export interface DataState {
  data: MatrixDataDTO["data"];
  aggregates: Partial<MatrixAggregates>;
}

export type SetMatrixDataFunction = (data: DataState & { saved?: boolean }) => void;

interface UseMatrixDataProps {
  studyId: string;
  path: string;
  aggregateTypes: AggregateType[];
  fetchFn?: fetchMatrixFn;
  rowCountSource?: RowCountSource;
}

export function useMatrixData({
  studyId,
  path,
  aggregateTypes,
  fetchFn,
  rowCountSource = "matrixIndex",
}: UseMatrixDataProps) {
  const [{ present: currentState }, { set, reset, undo, redo, canUndo, canRedo }] =
    useUndo<DataState>(
      {
        data: [],
        aggregates: { min: [], max: [], avg: [], total: [] },
      },
      { useCheckpoints: true },
    );

  const { t } = useTranslation();
  const [index, setIndex] = useState<MatrixIndex>();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error>();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [updateCount, setUpdateCount] = useState(0);

  const undoWrapper = useCallback(() => {
    undo();
    setUpdateCount((count) => count - 1);
  }, [undo]);

  const redoWrapper = useCallback(() => {
    redo();
    setUpdateCount((count) => count + 1);
  }, [redo]);

  const setMatrixData = useCallback<SetMatrixDataFunction>(
    ({ saved, ...data }) => {
      if (saved) {
        // When `saved` is true, it means the value is from the API. This is the return value after sending
        // the current present data to the API. So we set checkpoint to false to not add a new undo but replace
        // only the current present.
        set(data, false);
        setUpdateCount(0);
      } else {
        set(data, true);
        setUpdateCount((count) => count + 1);
      }
    },
    [set],
  );

  const fetchMatrix = useCallback(async () => {
    setIsLoading(true);

    try {
      const [matrix, index] = await Promise.all([
        // Use the custom fetch function if provided, else use the regular `/raw` API.
        fetchFn ? fetchFn(studyId) : getStudyData<MatrixDataDTO>(studyId, path, 1),
        getStudyMatrixIndex(studyId, path),
      ]);

      const newState = {
        data: matrix.data,
        aggregates: calculateMatrixAggregates({ matrix: matrix.data, types: aggregateTypes }),
      };

      reset(newState);
      setUpdateCount(0);

      setIndex(index);
      return { matrix, index };
    } catch (error) {
      setError(new Error(t("data.error.matrix")));
      enqueueErrorSnackbar(t("data.error.matrix"), toError(error));
    } finally {
      setIsLoading(false);
    }
  }, [fetchFn, studyId, path, aggregateTypes, reset, t, enqueueErrorSnackbar]);

  useEffect(() => {
    fetchMatrix();
  }, [fetchMatrix]);

  const dateTime = useMemo(() => {
    return index
      ? generateDateTime(index)
      : { values: [] as Date[], first_week_size: 0, level: TimeFrequency.Annual };
  }, [index]);

  return {
    // Current state
    currentState,
    aggregates: currentState.aggregates,
    updateCount: Math.abs(updateCount),

    // Metadata
    dateTime,
    rowCount: rowCountSource === "matrixIndex" ? index?.steps : currentState.data.length,
    matrixTimeFrequency: index?.level,

    // Status
    isDirty: updateCount !== 0,
    isLoading,
    error,

    // Actions
    setMatrixData,
    undo: undoWrapper,
    redo: redoWrapper,
    canUndo,
    canRedo,
    reload: fetchMatrix,
  };
}
