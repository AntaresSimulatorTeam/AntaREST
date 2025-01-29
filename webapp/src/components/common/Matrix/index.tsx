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

import { Box, Skeleton } from "@mui/material";
import MatrixGrid from "./components/MatrixGrid";
import { useMatrix } from "./hooks/useMatrix";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router";
import type { StudyMetadata } from "../../../types/types";
import { MatrixContainer, MatrixHeader, MatrixTitle } from "./styles";
import MatrixActions from "./components/MatrixActions";
import EmptyView from "../page/EmptyView";
import type { fetchMatrixFn } from "../../App/Singlestudy/explore/Modelization/Areas/Hydro/utils";
import type { AggregateConfig, RowCountSource } from "./shared/types";
import GridOffIcon from "@mui/icons-material/GridOff";
import MatrixUpload from "@/components/common/Matrix/components/MatrixUpload";

interface MatrixProps {
  url: string;
  title?: string;
  customRowHeaders?: string[];
  dateTimeColumn?: boolean;
  timeSeriesColumns?: boolean;
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
  title = "global.timeSeries",
  customRowHeaders = [],
  dateTimeColumn = true,
  timeSeriesColumns = true,
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

  // TODO: split `useMatrix` into smaller units
  const {
    data,
    aggregates,
    error,
    isLoading,
    isSubmitting,
    columns,
    dateTime,
    handleCellEdit,
    handleMultipleCellsEdit,
    handleUpload,
    handleSaveUpdates,
    pendingUpdatesCount,
    undo,
    redo,
    canUndo,
    canRedo,
    reload,
    rowCount,
  } = useMatrix(
    study.id,
    url,
    dateTimeColumn,
    timeSeriesColumns,
    rowHeaders,
    aggregateColumns,
    customColumns,
    colWidth,
    fetchMatrixData,
    rowCountSource,
  );

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
    <MatrixContainer>
      <MatrixHeader>
        <MatrixTitle>{t(title)}</MatrixTitle>
        <MatrixActions
          onImport={(_, index) => {
            setUploadType(index === 0 ? "file" : "database");
          }}
          onSave={handleSaveUpdates}
          studyId={study.id}
          path={url}
          disabled={data.length === 0}
          pendingUpdatesCount={pendingUpdatesCount}
          isSubmitting={isSubmitting}
          undo={undo}
          redo={redo}
          canUndo={canUndo}
          canRedo={canRedo}
          canImport={canImport}
        />
      </MatrixHeader>
      <Box sx={{ flex: 1 }}>
        {!data[0]?.length ? (
          <EmptyView title={t("matrix.message.matrixEmpty")} icon={GridOffIcon} />
        ) : (
          <MatrixGrid
            data={data}
            aggregates={aggregates}
            columns={columns}
            rows={rowCount ?? data.length}
            rowHeaders={customRowHeaders}
            dateTime={dateTime}
            onCellEdit={handleCellEdit}
            onMultipleCellsEdit={handleMultipleCellsEdit}
            readOnly={isSubmitting || readOnly}
            showPercent={showPercent}
          />
        )}
      </Box>
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
  );
}

export default Matrix;
