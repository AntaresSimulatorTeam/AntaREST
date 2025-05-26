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

import MatrixUpload from "@/components/common/Matrix/components/MatrixUpload";
import GridOffIcon from "@mui/icons-material/GridOff";
import { Box, Skeleton, Tooltip } from "@mui/material";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router";
import type { StudyMetadata } from "../../../types/types";
import type { fetchMatrixFn } from "../../App/Singlestudy/explore/Modelization/Areas/Hydro/utils";
import CustomScrollbar from "../CustomScrollbar";
import EmptyView from "../page/EmptyView";
import MatrixActions from "./components/MatrixActions";
import MatrixGrid from "./components/MatrixGrid";
import { MatrixProvider } from "./context/MatrixContext";
import { useMatrixColumns } from "./hooks/useMatrixColumns";
import { useMatrixData } from "./hooks/useMatrixData";
import { useMatrixMutations } from "./hooks/useMatrixMutations";
import { isNonEmptyMatrix, type AggregateConfig, type RowCountSource } from "./shared/types";
import { getAggregateTypes } from "./shared/utils";
import { MatrixContainer, MatrixHeader, MatrixTitle } from "./styles";

interface MatrixProps {
  url: string;
  title?: string;
  customRowHeaders?: string[];
  dateTimeColumn?: boolean;
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
}

function Matrix({
  url,
  title: titleProp,
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
  canImport = false,
  rowCountSource,
}: MatrixProps) {
  const { t } = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [uploadType, setUploadType] = useState<"file" | "database" | undefined>(undefined);
  const title = titleProp ?? t("global.timeSeries");

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
  } = useMatrixData({
    studyId: study.id,
    path: url,
    aggregateTypes,
    fetchFn: fetchMatrixData,
    rowCountSource,
  });

  const { isSubmitting, handleCellEdit, handleMultipleCellsEdit, handleUpload, handleSaveUpdates } =
    useMatrixMutations({
      studyId: study.id,
      path: url,
      currentState,
      setMatrixData,
      isDirty,
      reload,
      aggregateTypes,
    });

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
    return <Skeleton sx={{ height: 1, transform: "none" }} />;
  }

  if (error) {
    return <EmptyView title={error.message} />;
  }

  return (
    <MatrixProvider
      {...{
        data: currentState.data,
        currentState,
        isSubmitting,
        updateCount,
        setMatrixData,
        undo,
        redo,
        canUndo,
        canRedo,
        isDirty,
        aggregateTypes,
      }}
    >
      <MatrixContainer>
        {/* The <Box> allows to keep the height on vertical resize */}
        <Box>
          <CustomScrollbar>
            <MatrixHeader>
              <Tooltip title={title}>
                <MatrixTitle>{title}</MatrixTitle>
              </Tooltip>
              <MatrixActions
                studyId={study.id}
                path={url}
                disabled={currentState.data.length === 0}
                isTimeSeries={isTimeSeries}
                onSave={handleSaveUpdates}
                onMatrixUpdated={reload}
                canImport={canImport}
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
            readOnly={isSubmitting || readOnly}
            showPercent={showPercent}
          />
        ) : (
          <EmptyView title={t("matrix.message.matrixEmpty")} icon={GridOffIcon} />
        )}
        {uploadType === "file" && (
          <MatrixUpload
            studyId={study.id}
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
            studyId={study.id}
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
