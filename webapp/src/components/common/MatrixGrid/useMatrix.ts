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
  MatrixAggregates,
} from "./types";
import {
  aggregatesTheme,
  calculateMatrixAggregates,
  generateDataColumns,
  generateDateTime,
} from "./utils";
import useUndo from "use-undo";
import { GridCellKind } from "@glideapps/glide-data-grid";
import { importFile } from "../../../services/api/studies/raw";
import { fetchMatrixFn } from "../../App/Singlestudy/explore/Modelization/Areas/Hydro/utils";

interface DataState {
  data: MatrixDataDTO["data"];
  aggregates: MatrixAggregates;
  pendingUpdates: MatrixUpdateDTO[];
  updateCount: number;
}

export function useMatrix(
  studyId: string,
  url: string,
  enableDateTimeColumn: boolean,
  enableTimeSeriesColumns: boolean,
  enableAggregateColumns: boolean,
  enableRowHeaders?: boolean,
  customColumns?: string[] | readonly string[],
  colWidth?: number,
  fetchMatrixData?: fetchMatrixFn,
) {
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [columnCount, setColumnCount] = useState(0);
  const [index, setIndex] = useState<MatrixIndex | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<Error | undefined>(undefined);
  const [{ present: currentState }, { set: setState, undo, redo, canRedo }] =
    useUndo<DataState>({
      data: [],
      aggregates: { min: [], max: [], avg: [], total: [] },
      pendingUpdates: [],
      updateCount: 0,
    });

  const fetchMatrix = useCallback(
    async (loadingState = true) => {
      // !NOTE This is a temporary solution to ensure the matrix is up to date
      // TODO: Remove this once the matrix API is updated to return the correct data
      if (loadingState) {
        setIsLoading(true);
      }

      try {
        const [matrix, index] = await Promise.all([
          fetchMatrixData
            ? // If a custom fetch function is provided, use it
              fetchMatrixData(studyId)
            : getStudyData<MatrixDataDTO>(studyId, url, 1),
          getStudyMatrixIndex(studyId, url),
        ]);

        setState({
          data: matrix.data,
          aggregates: enableAggregateColumns
            ? calculateMatrixAggregates(matrix.data)
            : { min: [], max: [], avg: [], total: [] },
          pendingUpdates: [],
          updateCount: 0,
        });
        setColumnCount(matrix.columns.length);
        setIndex(index);
        setIsLoading(false);

        return {
          matrix,
          index,
        };
      } catch (error) {
        setError(new Error(t("data.error.matrix")));
        enqueueErrorSnackbar(t("data.error.matrix"), error as AxiosError);
      } finally {
        setIsLoading(false);
      }
    },
    [
      enableAggregateColumns,
      enqueueErrorSnackbar,
      fetchMatrixData,
      setState,
      studyId,
      url,
    ],
  );

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

    const baseColumns: EnhancedGridColumn[] = [];

    if (enableDateTimeColumn) {
      baseColumns.push({
        id: "date",
        title: "Date",
        type: ColumnTypes.DateTime,
        editable: false,
      });
    }

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
            editable: false,
            themeOverride: aggregatesTheme,
          },
          {
            id: "max",
            title: "Max",
            type: ColumnTypes.Aggregate,
            editable: false,
            themeOverride: aggregatesTheme,
          },
          {
            id: "avg",
            title: "Avg",
            type: ColumnTypes.Aggregate,
            editable: false,
            themeOverride: aggregatesTheme,
          },
        ]
      : [];

    return [...baseColumns, ...dataColumns, ...aggregateColumns];
  }, [
    currentState.data,
    enableDateTimeColumn,
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
          if (value.kind === GridCellKind.Number && value.data !== undefined) {
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

      // Recalculate aggregates with the updated data
      const newAggregates = enableAggregateColumns
        ? calculateMatrixAggregates(updatedData)
        : { min: [], max: [], avg: [], total: [] };

      setState({
        data: updatedData,
        aggregates: newAggregates,
        pendingUpdates: [...currentState.pendingUpdates, ...newUpdates],
        updateCount: currentState.updateCount + 1 || 1,
      });
    },
    [
      currentState.data,
      currentState.pendingUpdates,
      currentState.updateCount,
      enableAggregateColumns,
      setState,
    ],
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

      setState({
        ...currentState,
        pendingUpdates: [],
        updateCount: 0,
      });

      enqueueSnackbar(t("matrix.success.matrixUpdate"), {
        variant: "success",
      });

      // !NOTE This is a temporary solution to ensure the matrix is up to date
      // TODO: Remove this once the matrix API is updated to return the correct data
      await fetchMatrix(false);
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
    aggregates: currentState.aggregates,
    error,
    isLoading,
    isSubmitting,
    columns,
    dateTime,
    handleCellEdit,
    handleMultipleCellsEdit,
    handleImport,
    handleSaveUpdates,
    pendingUpdatesCount: currentState.updateCount,
    undo: handleUndo,
    redo: handleRedo,
    canUndo: canUndoChanges,
    canRedo,
  };
}
