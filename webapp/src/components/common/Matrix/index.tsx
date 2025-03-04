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

import { Divider, Skeleton } from "@mui/material";
import MatrixGrid from "./components/MatrixGrid";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router";
import type { StudyMetadata } from "../../../types/types";
import { MatrixContainer, MatrixHeader, MatrixTitle } from "./styles";
import MatrixActions from "./components/MatrixActions";
import EmptyView from "../page/EmptyView";
import type { fetchMatrixFn } from "../../App/Singlestudy/explore/Modelization/Areas/Hydro/utils";
import { isNonEmptyMatrix, type AggregateConfig, type RowCountSource } from "./shared/types";
import GridOffIcon from "@mui/icons-material/GridOff";
import MatrixUpload from "@/components/common/Matrix/components/MatrixUpload";
import { MatrixProvider } from "./context/MatrixContext";
import { useMatrixData } from "./hooks/useMatrixData";
import { getAggregateTypes } from "./shared/utils";
import { useMatrixMutations } from "./hooks/useMatrixMutations";
import { useMatrixColumns } from "./hooks/useMatrixColumns";

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
  title = "global.timeSeries",
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

  const aggregateTypes = useMemo(
    () => getAggregateTypes(aggregateColumns || []),
    [aggregateColumns],
  );

  const {
    currentState,
    dateTime,
    aggregates,
    isLoading,
    error,
    updateCount,
    setMatrixData,
    reset,
    undo,
    redo,
    canUndo,
    canRedo,
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
      reset,
      canUndo,
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
        reset,
        undo,
        redo,
        canUndo,
        canRedo,
      }}
    >
      <MatrixContainer>
        <MatrixHeader>
          <MatrixTitle>{t(title)}</MatrixTitle>
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
        <Divider sx={{ width: 1, mt: 1, mb: 2 }} />
        {isNonEmptyMatrix(currentState.data) ? (
          <MatrixGrid
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
