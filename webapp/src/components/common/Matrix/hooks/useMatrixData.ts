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
import type { MatrixIndex } from "@/common/types";
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
  updateCount: number;
}

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
  const [{ present: currentState }, { set: setState, undo, redo, canRedo }] = useUndo<DataState>({
    data: [],
    aggregates: { min: [], max: [], avg: [], total: [] },
    updateCount: 0,
  });
  const [index, setIndex] = useState<MatrixIndex>();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error>();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const fetchMatrix = useCallback(async () => {
    try {
      const [matrix, index] = await Promise.all([
        // Use the custom fetch function if provided, else use the regular `/raw` API.
        fetchFn ? fetchFn(studyId) : getStudyData<MatrixDataDTO>(studyId, path, 1),
        getStudyMatrixIndex(studyId, path),
      ]);

      setState({
        data: matrix.data,
        aggregates: calculateMatrixAggregates({ matrix: matrix.data, types: aggregateTypes }),
        updateCount: 0,
      });

      setIndex(index);
      return { matrix, index };
    } catch (error) {
      setError(new Error(t("data.error.matrix")));
      enqueueErrorSnackbar(t("data.error.matrix"), toError(error));
    } finally {
      setIsLoading(false);
    }
  }, [fetchFn, studyId, path, setState, aggregateTypes, enqueueErrorSnackbar]);

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
    updateCount: currentState.updateCount,

    // Metadata
    dateTime,
    rowCount: rowCountSource === "matrixIndex" ? index?.steps : currentState.data.length,

    // Status
    isLoading,
    error,

    // Actions
    setState,
    undo,
    redo,
    canUndo: currentState.updateCount > 0,
    canRedo,
    reload: fetchMatrix,
  };
}
