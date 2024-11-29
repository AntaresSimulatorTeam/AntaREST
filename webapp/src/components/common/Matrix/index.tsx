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

import { Divider, Skeleton } from "@mui/material";
import MatrixGrid from "./components/MatrixGrid";
import { useMatrix } from "./hooks/useMatrix";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../common/types";
import { MatrixContainer, MatrixHeader, MatrixTitle } from "./styles";
import MatrixActions from "./components/MatrixActions";
import EmptyView from "../page/SimpleContent";
import { fetchMatrixFn } from "../../App/Singlestudy/explore/Modelization/Areas/Hydro/utils";
import { AggregateConfig } from "./shared/types";
import { GridOff } from "@mui/icons-material";
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
}: MatrixProps) {
  const { t } = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [uploadType, setUploadType] = useState<"file" | "database" | undefined>(
    undefined,
  );

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
      <Divider sx={{ width: 1, mt: 1, mb: 2 }} />
      {!data[0]?.length ? (
        <EmptyView title={t("matrix.message.matrixEmpty")} icon={GridOff} />
      ) : (
        <MatrixGrid
          data={data}
          aggregates={aggregates}
          columns={columns}
          rows={data.length}
          rowHeaders={customRowHeaders}
          dateTime={dateTime}
          onCellEdit={handleCellEdit}
          onMultipleCellsEdit={handleMultipleCellsEdit}
          readOnly={isSubmitting || readOnly}
          showPercent={showPercent}
        />
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
  );
}

export default Matrix;
