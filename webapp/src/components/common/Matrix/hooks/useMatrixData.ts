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

import { useState, useCallback, useEffect, useMemo } from "react";
import { t } from "i18next";
import type { MatrixIndex } from "@/types/types";
import { getStudyMatrixIndex } from "@/services/api/matrix";
import { getStudyData } from "@/services/api/study";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import type {
  MatrixDataDTO,
  AggregateType,
  MatrixAggregates,
  RowCountSource,
} from "../shared/types";
import { calculateMatrixAggregates, generateDateTime } from "../shared/utils";
import type { fetchMatrixFn } from "@/components/App/Singlestudy/explore/Modelization/Areas/Hydro/utils";
import { toError } from "@/utils/fnUtils";
import useUndo from "use-undo";

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
  }, [fetchFn, studyId, path, reset, aggregateTypes, enqueueErrorSnackbar]);

  useEffect(() => {
    fetchMatrix();
  }, [fetchMatrix]);

  const dateTime = useMemo(() => {
    return index ? generateDateTime(index) : [];
  }, [index]);

  return {
    // Current state
    currentState,
    aggregates: currentState.aggregates,
    updateCount: Math.abs(updateCount),

    // Metadata
    dateTime,
    rowCount: rowCountSource === "matrixIndex" ? index?.steps : currentState.data.length,

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
