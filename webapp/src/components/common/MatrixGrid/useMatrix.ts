import { useMemo } from "react";
import { Item } from "@glideapps/glide-data-grid";
import { AxiosError } from "axios";
import { enqueueSnackbar } from "notistack";
import { t } from "i18next";
import { MatrixEditDTO, Operator } from "../../../common/types";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import usePromiseWithSnackbarError from "../../../hooks/usePromiseWithSnackbarError";
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

  const {
    data: matrixData,
    isLoading: isLoadingMatrix,
    reload: reloadMatrix,
  } = usePromiseWithSnackbarError(
    () => getStudyData<MatrixData>(studyId, url),
    {
      errorMessage: t("data.error.matrix"),
      deps: [studyId, url],
    },
  );

  const { data: matrixIndex, isLoading: isLoadingIndex } =
    usePromiseWithSnackbarError(() => getStudyMatrixIndex(studyId, url), {
      errorMessage: t("matrix.error.failedToretrieveIndex"),
      deps: [studyId, url, matrixData],
    });

  const dateTime = useMemo(() => {
    return matrixIndex ? generateDateTime(matrixIndex as TimeMetadataDTO) : [];
  }, [matrixIndex]);

  const columns: EnhancedGridColumn[] = useMemo(() => {
    if (!matrixData) {
      return [];
    }

    const baseColumns = [
      {
        id: "date",
        title: "Date",
        type: ColumnDataType.DateTime,
        width: 150,
        editable: false,
      },
    ];

    const dataColumns = enableTimeSeriesColumns
      ? generateTimeSeriesColumns({ count: matrixData.columns.length })
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
  }, [matrixData, enableTimeSeriesColumns, enableAggregateColumns]);

  const handleCellEdit = async function (coordinates: Item, newValue: number) {
    const [row, col] = coordinates;

    const update: MatrixEditDTO[] = [
      {
        coordinates: [[col, row]],
        operation: {
          operation: Operator.EQ,
          value: newValue,
        },
      },
    ];

    try {
      await editMatrix(studyId, url, update);
      reloadMatrix();
      enqueueSnackbar(t("matrix.success.matrixUpdate"), {
        variant: "success",
      });
    } catch (e) {
      enqueueErrorSnackbar(t("matrix.error.matrixUpdate"), e as AxiosError);
    }
  };

  const handleMultipleCellsEdit = async function (
    newValues: Array<{ coordinates: Item; value: number }>,
    fillPattern?: CellFillPattern,
  ) {
    const updates = newValues.map(({ coordinates, value }) => ({
      coordinates: [[coordinates[1], coordinates[0]]],
      operation: {
        operation: Operator.EQ,
        value,
      },
    }));

    try {
      await editMatrix(studyId, url, updates);
      reloadMatrix();
      enqueueSnackbar(t("matrix.success.matrixUpdate"), {
        variant: "success",
      });
    } catch (e) {
      enqueueErrorSnackbar(t("matrix.error.matrixUpdate"), e as AxiosError);
    }
  };

  const handleImport = async (file: File) => {
    try {
      await importFile(file, studyId, url);
      reloadMatrix();
      enqueueSnackbar(t("matrix.success.import"), { variant: "success" });
    } catch (e) {
      enqueueErrorSnackbar(t("matrix.error.import"), e as Error);
    }
  };

  return {
    matrixData,
    isLoading: isLoadingMatrix || isLoadingIndex,
    columns,
    dateTime,
    handleCellEdit,
    handleMultipleCellsEdit,
    handleImport,
    reloadMatrix,
  };
}
