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
import { MatrixIndex } from "../../../../../common/types";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import {
  getStudyMatrixIndex,
  updateMatrix,
} from "../../../../../services/api/matrix";
import { getStudyData } from "../../../../../services/api/study";
import {
  EnhancedGridColumn,
  MatrixDataDTO,
  GridUpdate,
  MatrixUpdateDTO,
  MatrixAggregates,
  AggregateConfig,
} from "../../shared/types";
import {
  calculateMatrixAggregates,
  generateDataColumns,
  generateDateTime,
  getAggregateTypes,
} from "../../shared/utils";
import useUndo from "use-undo";
import { GridCellKind } from "@glideapps/glide-data-grid";
import { uploadFile } from "../../../../../services/api/studies/raw";
import { fetchMatrixFn } from "../../../../App/Singlestudy/explore/Modelization/Areas/Hydro/utils";
import usePrompt from "../../../../../hooks/usePrompt";
import { Aggregate, Column, Operation } from "../../shared/constants";
import { aggregatesTheme } from "../../styles";

interface DataState {
  data: MatrixDataDTO["data"];
  aggregates: Partial<MatrixAggregates>;
  pendingUpdates: MatrixUpdateDTO[];
  updateCount: number;
}

export function useMatrix(
  studyId: string,
  url: string,
  dateTimeColumn: boolean,
  timeSeriesColumns: boolean,
  enableRowHeaders?: boolean,
  aggregatesConfig?: AggregateConfig,
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

  // Determine the aggregate types to display in the matrix
  const aggregateTypes = useMemo(
    () => getAggregateTypes(aggregatesConfig || []),
    [aggregatesConfig],
  );

  // Display warning prompts to prevent unintended navigation
  // 1. When the matrix is currently being submitted
  usePrompt(t("form.submit.inProgress"), isSubmitting);
  // 2. When there are unsaved changes in the matrix
  usePrompt(t("form.changeNotSaved"), currentState.pendingUpdates.length > 0);

  const fetchMatrix = async (loadingState = true) => {
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
        aggregates: calculateMatrixAggregates(matrix.data, aggregateTypes),
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
  };

  useEffect(() => {
    fetchMatrix();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [studyId, url, aggregateTypes, fetchMatrixData]);

  const dateTime = useMemo(() => {
    return index ? generateDateTime(index) : [];
  }, [index]);

  const columns = useMemo(() => {
    if (!currentState.data) {
      return [];
    }

    const baseColumns: EnhancedGridColumn[] = [];

    if (dateTimeColumn) {
      baseColumns.push({
        id: "date",
        title: "Date",
        type: Column.DateTime,
        editable: false,
        themeOverride: { bgCell: "#2D2E40" },
      });
    }

    if (enableRowHeaders) {
      baseColumns.unshift({
        id: "rowHeaders",
        title: "",
        type: Column.Text,
        editable: false,
      });
    }

    const dataColumns = generateDataColumns({
      timeSeriesColumns,
      count: columnCount,
      customColumns,
      width: colWidth,
    });

    const aggregatesColumns: EnhancedGridColumn[] = aggregateTypes.map(
      (aggregateType) => ({
        id: aggregateType,
        title: aggregateType.charAt(0).toUpperCase() + aggregateType.slice(1), // Capitalize first letter
        type: Column.Aggregate,
        editable: false,
        themeOverride:
          aggregateType === Aggregate.Avg
            ? aggregatesTheme
            : { ...aggregatesTheme, bgCell: "#464770" },
      }),
    );

    return [...baseColumns, ...dataColumns, ...aggregatesColumns];
  }, [
    currentState.data,
    dateTimeColumn,
    enableRowHeaders,
    timeSeriesColumns,
    columnCount,
    customColumns,
    colWidth,
    aggregateTypes,
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
                operation: Operation.Eq,
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
      const newAggregates = calculateMatrixAggregates(
        updatedData,
        aggregateTypes,
      );

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
      aggregateTypes,
      setState,
    ],
  );

  const handleCellEdit = function (update: GridUpdate) {
    applyUpdates([update]);
  };

  const handleMultipleCellsEdit = function (updates: GridUpdate[]) {
    applyUpdates(updates);
  };

  const handleUpload = async (file: File) => {
    try {
      await uploadFile({ file, studyId, path: url });
      // TODO: update the API to return the uploaded file data and remove this
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
    handleUpload,
    handleSaveUpdates,
    pendingUpdatesCount: currentState.updateCount,
    undo: handleUndo,
    redo: handleRedo,
    canUndo: canUndoChanges,
    canRedo,
    reload: fetchMatrix,
    // Use the matrix index 'steps' field to determine the number of rows
    // This ensures consistent row display (8760 for hourly, 365 for daily/weekly)
    // rather than using data.length which can vary for Binding Constraints (8784/366)
    rowCount: index?.steps,
  };
}
