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

export function useMatrix(
  studyId: string,
  url: string,
  enableTimeSeriesColumns: boolean,
  enableAggregateColumns: boolean,
) {
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [data, setData] = useState<MatrixData["data"]>([]);
  const [columnCount, setColumnCount] = useState(0);
  const [index, setIndex] = useState<MatrixIndex | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<Error | undefined>(undefined);
  const [pendingUpdates, setPendingUpdates] = useState<MatrixEditDTO[]>([]);

  const fetchMatrix = useCallback(async () => {
    setIsLoading(true);
    setError(undefined);
    try {
      const [matrix, index] = await Promise.all([
        getStudyData<MatrixData>(studyId, url),
        getStudyMatrixIndex(studyId, url),
      ]);

      setData(matrix.data);
      setColumnCount(matrix.columns.length);
      setIndex(index);
      setIsLoading(false);
    } catch (error) {
      setError(new Error(t("data.error.matrix")));
      enqueueErrorSnackbar(t("data.error.matrix"), error as AxiosError);
      setIsLoading(false);
    }
  }, [enqueueErrorSnackbar, studyId, url]);

  useEffect(() => {
    fetchMatrix();
  }, [fetchMatrix]);

  const dateTime = useMemo(() => {
    return index ? generateDateTime(index as TimeMetadataDTO) : [];
  }, [index]);

  const columns: EnhancedGridColumn[] = useMemo(() => {
    if (!data) {
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
  }, [data, enableTimeSeriesColumns, columnCount, enableAggregateColumns]);

  const updateDataAndPendingUpdates = (
    updates: Array<{ coordinates: Item; value: number }>,
  ) => {
    setData((prevData) => {
      const newData = prevData.map((col) => [...col]);
      updates.forEach(({ coordinates: [row, col], value }) => {
        newData[col][row] = value;
      });
      return newData;
    });

    setPendingUpdates((prevUpdates) => [
      ...prevUpdates,
      ...updates.map(({ coordinates: [row, col], value }) => ({
        coordinates: [[col, row]],
        operation: {
          operation: Operator.EQ,
          value,
        },
      })),
    ]);
  };

  const handleCellEdit = function (coordinates: Item, newValue: number) {
    updateDataAndPendingUpdates([{ coordinates, value: newValue }]);
  };

  const handleMultipleCellsEdit = function (
    newValues: Array<{ coordinates: Item; value: number }>,
    fillPattern?: CellFillPattern,
  ) {
    updateDataAndPendingUpdates(newValues);
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
    if (pendingUpdates.length > 0) {
      setIsSubmitting(true);
      setError(undefined);
      try {
        await editMatrix(studyId, url, pendingUpdates);
        setPendingUpdates([]);
        enqueueSnackbar(t("matrix.success.matrixUpdate"), {
          variant: "success",
        });
      } catch (error) {
        setError(new Error(t("matrix.error.matrixUpdate")));
        enqueueErrorSnackbar(
          t("matrix.error.matrixUpdate"),
          error as AxiosError,
        );
      } finally {
        await fetchMatrix();
        setIsSubmitting(false);
      }
    }
  };

  return {
    data,
    error,
    isLoading,
    isSubmitting,
    columns,
    dateTime,
    handleCellEdit,
    handleMultipleCellsEdit,
    handleImport,
    handleSaveUpdates,
    pendingUpdatesCount: pendingUpdates.length,
  };
}
