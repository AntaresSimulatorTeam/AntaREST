import { useCallback, useEffect, useMemo, useState } from "react";
import { Item } from "@glideapps/glide-data-grid";
import { AxiosError } from "axios";
import { enqueueSnackbar } from "notistack";
import { t } from "i18next";
import { MatrixEditDTO, MatrixIndex, Operator } from "../../../common/types";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import { getStudyMatrixIndex, editMatrix } from "../../../services/api/matrix";
import { getStudyData, importFile } from "../../../services/api/study";
import {
  EnhancedGridColumn,
  CellFillPattern,
  TimeMetadataDTO,
  MatrixData,
} from "./types";
import {
  generateDateTime,
  ColumnDataType,
  generateTimeSeriesColumns,
} from "./utils";
import useUndo from "use-undo";

interface DataState {
  data: number[][];
  pendingUpdates: MatrixEditDTO[];
}

export function useMatrix(
  studyId: string,
  url: string,
  enableTimeSeriesColumns: boolean,
  enableAggregateColumns: boolean,
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
        getStudyData<MatrixData>(studyId, url),
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
    return index ? generateDateTime(index as TimeMetadataDTO) : [];
  }, [index]);

  const columns: EnhancedGridColumn[] = useMemo(() => {
    if (!currentState.data) {
      return [];
    }

    const baseColumns = [
      {
        id: "date",
        title: "Date",
        type: ColumnDataType.DateTime,
        editable: false,
      },
    ];

    const dataColumns = enableTimeSeriesColumns
      ? generateTimeSeriesColumns({ count: columnCount })
      : [];

    const aggregateColumns = enableAggregateColumns
      ? [
          {
            id: "min",
            title: "Min",
            type: ColumnDataType.Aggregate,
            width: 50,
            editable: false,
          },
          {
            id: "max",
            title: "Max",
            type: ColumnDataType.Aggregate,
            width: 50,
            editable: false,
          },
          {
            id: "avg",
            title: "Avg",
            type: ColumnDataType.Aggregate,
            width: 50,
            editable: false,
          },
        ]
      : [];

    return [...baseColumns, ...dataColumns, ...aggregateColumns];
  }, [
    currentState.data,
    enableTimeSeriesColumns,
    columnCount,
    enableAggregateColumns,
  ]);

  // Apply updates to the matrix data and store them in the pending updates list
  const applyUpdates = useCallback(
    (updates: Array<{ coordinates: Item; value: number }>) => {
      if (!currentState.data) {
        return;
      }

      const updatedData = currentState.data.map((col) => [...col]);

      const newUpdates = updates.map(({ coordinates: [row, col], value }) => {
        updatedData[col][row] = value;

        return {
          coordinates: [[col, row]],
          operation: {
            operation: Operator.EQ,
            value,
          },
        };
      });

      setState({
        data: updatedData,
        pendingUpdates: [...currentState.pendingUpdates, ...newUpdates],
      });
    },
    [currentState, setState],
  );

  const handleCellEdit = function (coordinates: Item, newValue: number) {
    applyUpdates([{ coordinates, value: newValue }]);
  };

  const handleMultipleCellsEdit = function (
    newValues: Array<{ coordinates: Item; value: number }>,
    fillPattern?: CellFillPattern,
  ) {
    applyUpdates(newValues);
  };

  const handleImport = async (file: File) => {
    try {
      await importFile(file, studyId, url);

      enqueueSnackbar(t("matrix.success.import"), { variant: "success" });
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
      await editMatrix(studyId, url, currentState.pendingUpdates);
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
