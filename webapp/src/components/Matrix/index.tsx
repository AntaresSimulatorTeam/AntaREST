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
import MatrixUpload from "@/components/Matrix/components/MatrixUpload";
import type { fetchMatrixFn } from "@/routes/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/hydro/-utils";
import type { StudyMetadata } from "@/types/types";
import GridOffIcon from "@mui/icons-material/GridOff";
import { Box, Tooltip } from "@mui/material";
import { useCallback, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import CustomScrollbar from "../CustomScrollbar";
import EmptyView from "../page/EmptyView";
import ErrorView from "../page/ErrorView";
import MatrixActions from "./components/MatrixActions";
import MatrixGrid from "./components/MatrixGrid";
import { MatrixProvider } from "./context/MatrixContext";
import { useMatrixColumns } from "./hooks/useMatrixColumns";
import { useMatrixData } from "./hooks/useMatrixData";
import { useMatrixMutations } from "./hooks/useMatrixMutations";
import { type AggregateConfig, isNonEmptyMatrix, type RowCountSource } from "./shared/types";
import { calculateMatrixAggregates, getAggregateTypes } from "./shared/utils";
import { MatrixContainer, MatrixHeader, MatrixTitle } from "./styles";

interface MatrixProps {
  studyId: StudyMetadata["id"];
  url: string;
  title?: string;
  customRowHeaders?: string[];
  dateTimeColumn?: boolean;
  /**
   * Enables time series features like temporal filters, resize, and calculated columns.
   * Note: For specific cases (e.g., hourly time series that shouldn't resize), use enableFilters/enableResize to override.
   */
  isTimeSeries?: boolean;
  aggregateColumns?: AggregateConfig;
  rowHeaders?: boolean;
  showPercent?: boolean;
  readOnly?: boolean;
  customColumns?: string[] | readonly string[];
  colWidth?: number;
  fetchMatrixData?: fetchMatrixFn;
  canImport?: boolean;
  rowCountSource?: RowCountSource;
  /**
   * Feature flag for data filtering functionality.
   * Useful for matrices that need filtering but can't be resized.
   */
  enableFilters?: boolean;
  /**
   * Feature flag for data resizing functionality.
   * Some matrices have temporal structure but fixed dimensions.
   */
  enableResize?: boolean;
}

function Matrix({
  studyId,
  url,
  title,
  customRowHeaders = [],
  dateTimeColumn = true,
  isTimeSeries = true,
  aggregateColumns = false,
  rowHeaders = customRowHeaders.length > 0,
  showPercent = false,
  readOnly = false,
  customColumns,
  colWidth,
  fetchMatrixData,
  canImport = true,
  rowCountSource,
  enableFilters = isTimeSeries,
  enableResize = isTimeSeries,
}: MatrixProps) {
  const { t } = useTranslation();
  const [uploadType, setUploadType] = useState<"file" | "database" | undefined>(undefined);

  const aggregateTypes = useMemo(
    () => getAggregateTypes(aggregateColumns || []),
    [aggregateColumns],
  );

  const {
    currentState,
    updateCount,
    dateTime,
    aggregates,
    isLoading,
    error,
    setMatrixData,
    undo,
    redo,
    canUndo,
    canRedo,
    isDirty,
    reload,
    rowCount,
    matrixTimeFrequency,
  } = useMatrixData({
    studyId,
    path: url,
    aggregateTypes,
    fetchFn: fetchMatrixData,
    rowCountSource,
  });

  const { isSubmitting, handleCellEdit, handleMultipleCellsEdit, handleUpload, handleSaveUpdates } =
    useMatrixMutations({
      studyId,
      path: url,
      currentState,
      setMatrixData,
      isDirty,
      reload,
      aggregateTypes,
    });

  const handleBulkPaste = useCallback(
    (newData: number[][]) => {
      const newAggregates = calculateMatrixAggregates({ matrix: newData, types: aggregateTypes });
      setMatrixData({ data: newData, aggregates: newAggregates });
    },
    [setMatrixData, aggregateTypes],
  );

  const columns = useMatrixColumns({
    data: currentState.data,
    dateTimeColumn,
    enableRowHeaders: rowHeaders,
    isTimeSeries,
    customColumns,
    colWidth,
    aggregateTypes,
  });

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (isLoading) {
    return <DataGridSkeleton />;
  }

  if (error) {
    return <ErrorView error={error} />;
  }

  return (
    <MatrixProvider
      currentState={currentState}
      isSubmitting={isSubmitting}
      updateCount={updateCount}
      aggregateTypes={aggregateTypes}
      setMatrixData={setMatrixData}
      undo={undo}
      redo={redo}
      canUndo={canUndo}
      canRedo={canRedo}
      isDirty={isDirty}
    >
      <MatrixContainer>
        <Box>
          <CustomScrollbar>
            <MatrixHeader>
              <Tooltip title={title}>
                <MatrixTitle>{title || t("global.timeSeries")}</MatrixTitle>
              </Tooltip>
              <MatrixActions
                studyId={studyId}
                path={url}
                disabled={currentState.data.length === 0}
                dateTime={dateTime}
                isTimeSeries={isTimeSeries}
                timeFrequency={matrixTimeFrequency}
                onSave={handleSaveUpdates}
                onMatrixUpdated={reload}
                canImport={canImport}
                enableFilters={enableFilters}
                enableResize={enableResize}
                onImport={(_, index) => {
                  setUploadType(index === 0 ? "file" : "database");
                }}
              />
            </MatrixHeader>
          </CustomScrollbar>
        </Box>
        {isNonEmptyMatrix(currentState.data) ? (
          <MatrixGrid
            key={`matrix-${url}`}
            data={currentState.data}
            aggregates={aggregates}
            columns={columns}
            rows={rowCount ?? currentState.data.length}
            rowHeaders={customRowHeaders}
            dateTime={dateTime}
            onCellEdit={handleCellEdit}
            onMultipleCellsEdit={handleMultipleCellsEdit}
            onBulkPaste={handleBulkPaste}
            readOnly={isSubmitting || readOnly}
            showPercent={showPercent}
          />
        ) : (
          <EmptyView title={t("matrix.message.matrixEmpty")} icon={GridOffIcon} />
        )}
        {uploadType === "file" && (
          <MatrixUpload
            studyId={studyId}
            path={url}
            type="file"
            open={true}
            onClose={() => setUploadType(undefined)}
            onFileUpload={handleUpload}
            fileOptions={{
              accept: { "text/*": [".csv", ".tsv", ".txt"] },
              dropzoneText: t("matrix.message.importHint"),
            }}
          />
        )}
        {uploadType === "database" && (
          <MatrixUpload
            studyId={studyId}
            path={url}
            type="database"
            open={true}
            onClose={() => {
              setUploadType(undefined);
              reload();
            }}
          />
        )}
      </MatrixContainer>
    </MatrixProvider>
  );
}

export default Matrix;
