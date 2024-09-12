/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { useCallback, useEffect, useMemo, useState } from "react";
import { AxiosError } from "axios";
import { enqueueSnackbar } from "notistack";
import { t } from "i18next";
import { MatrixIndex, Operator } from "../../../common/types";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import {
  getStudyMatrixIndex,
  updateMatrix,
} from "../../../services/api/matrix";
import { getStudyData } from "../../../services/api/study";
import {
  EnhancedGridColumn,
  MatrixDataDTO,
  ColumnTypes,
  GridUpdate,
  MatrixUpdateDTO,
} from "./types";
import { generateDataColumns, generateDateTime } from "./utils";
import useUndo from "use-undo";
import { GridCellKind } from "@glideapps/glide-data-grid";
import { importFile } from "../../../services/api/studies/raw";

interface DataState {
  data: number[][];
  pendingUpdates: MatrixUpdateDTO[];
}

export function useMatrix(
  studyId: string,
  url: string,
  enableTimeSeriesColumns: boolean,
  enableAggregateColumns: boolean,
  enableRowHeaders?: boolean,
  customColumns?: string[] | readonly string[],
  colWidth?: number,
) {
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [columnCount, setColumnCount] = useState(0);
  const [index, setIndex] = useState<MatrixIndex | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<Error | undefined>(undefined);
  const [{ present: currentState }, { set: setState, undo, redo, canRedo }] =
    useUndo<DataState>({ data: [], pendingUpdates: [] });

  const fetchMatrix = useCallback(async () => {
    setIsLoading(true);
    try {
      const [matrix, index] = await Promise.all([
        getStudyData<MatrixDataDTO>(studyId, url),
        getStudyMatrixIndex(studyId, url),
      ]);

      setState({ data: matrix.data, pendingUpdates: [] });
      setColumnCount(matrix.columns.length);
      setIndex(index);
      setIsLoading(false);
    } catch (error) {
      setError(new Error(t("data.error.matrix")));
      enqueueErrorSnackbar(t("data.error.matrix"), error as AxiosError);
    } finally {
      setIsLoading(false);
    }
  }, [enqueueErrorSnackbar, setState, studyId, url]);

  useEffect(() => {
    fetchMatrix();
  }, [fetchMatrix]);

  const dateTime = useMemo(() => {
    return index ? generateDateTime(index) : [];
  }, [index]);

  const columns = useMemo(() => {
    if (!currentState.data) {
      return [];
    }

    const baseColumns: EnhancedGridColumn[] = [
      {
        id: "date",
        title: "Date",
        type: ColumnTypes.DateTime,
        editable: false,
      },
    ];

    if (enableRowHeaders) {
      baseColumns.unshift({
        id: "rowHeaders",
        title: "",
        type: ColumnTypes.Text,
        editable: false,
      });
    }

    const dataColumns = generateDataColumns(
      enableTimeSeriesColumns,
      columnCount,
      customColumns,
      colWidth,
    );

    const aggregateColumns: EnhancedGridColumn[] = enableAggregateColumns
      ? [
          {
            id: "min",
            title: "Min",
            type: ColumnTypes.Aggregate,
            width: 50,
            editable: false,
          },
          {
            id: "max",
            title: "Max",
            type: ColumnTypes.Aggregate,
            width: 50,
            editable: false,
          },
          {
            id: "avg",
            title: "Avg",
            type: ColumnTypes.Aggregate,
            width: 50,
            editable: false,
          },
        ]
      : [];

    return [...baseColumns, ...dataColumns, ...aggregateColumns];
  }, [
    currentState.data,
    enableRowHeaders,
    enableTimeSeriesColumns,
    columnCount,
    customColumns,
    colWidth,
    enableAggregateColumns,
  ]);

  // Apply updates to the matrix data and store them in the pending updates list
  const applyUpdates = useCallback(
    (updates: GridUpdate[]) => {
      const updatedData = currentState.data.map((col) => [...col]);

      const newUpdates: MatrixUpdateDTO[] = updates
        .map(({ coordinates: [row, col], value }) => {
          if (value.kind === GridCellKind.Number && value.data) {
            updatedData[col][row] = value.data;

            return {
              coordinates: [[col, row]],
              operation: {
                operation: Operator.EQ,
                value: value.data,
              },
            };
          }

          return null;
        })
        .filter(
          (update): update is NonNullable<typeof update> => update !== null,
        );

      setState({
        data: updatedData,
        pendingUpdates: [...currentState.pendingUpdates, ...newUpdates],
      });
    },
    [currentState, setState],
  );

  const handleCellEdit = function (update: GridUpdate) {
    applyUpdates([update]);
  };

  const handleMultipleCellsEdit = function (updates: GridUpdate[]) {
    applyUpdates(updates);
  };

  const handleImport = async (file: File) => {
    try {
      await importFile({ file, studyId, path: url });
      await fetchMatrix();
    } catch (e) {
      enqueueErrorSnackbar(t("matrix.error.import"), e as Error);
    }
  };

  const handleSaveUpdates = async () => {
    if (!currentState.pendingUpdates.length) {
      return;
    }

    setIsSubmitting(true);
    try {
      await updateMatrix(studyId, url, currentState.pendingUpdates);
      setState({ data: currentState.data, pendingUpdates: [] });
      enqueueSnackbar(t("matrix.success.matrixUpdate"), {
        variant: "success",
      });
    } catch (error) {
      setError(new Error(t("matrix.error.matrixUpdate")));
      enqueueErrorSnackbar(t("matrix.error.matrixUpdate"), error as AxiosError);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUndo = useCallback(() => {
    undo();
  }, [undo]);

  const handleRedo = useCallback(() => {
    redo();
  }, [redo]);

  const canUndoChanges = useMemo(
    () => currentState.pendingUpdates.length > 0,
    [currentState.pendingUpdates],
  );

  return {
    data: currentState.data,
    error,
    isLoading,
    isSubmitting,
    columns,
    dateTime,
    handleCellEdit,
    handleMultipleCellsEdit,
    handleImport,
    handleSaveUpdates,
    pendingUpdatesCount: currentState.pendingUpdates.length,
    undo: handleUndo,
    redo: handleRedo,
    canUndo: canUndoChanges,
    canRedo,
  };
}
