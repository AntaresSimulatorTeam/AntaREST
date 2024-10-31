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

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router";

import { Divider, Skeleton } from "@mui/material";

import { StudyMetadata } from "@/common/types";
import { fetchMatrixFn } from "@/components/App/Singlestudy/explore/Modelization/Areas/Hydro/utils";

import ImportDialog from "../dialogs/ImportDialog";
import EmptyView from "../page/SimpleContent";

import MatrixActions from "./components/MatrixActions";
import MatrixGrid from "./components/MatrixGrid";
import { useMatrix } from "./hooks/useMatrix";
import { AggregateConfig } from "./shared/types";
import { MatrixContainer, MatrixHeader, MatrixTitle } from "./styles";

interface MatrixProps {
  url: string;
  title?: string;
  customRowHeaders?: string[];
  enableDateTimeColumn?: boolean;
  enableTimeSeriesColumns?: boolean;
  aggregateColumns?: AggregateConfig;
  rowHeaders?: boolean;
  showPercent?: boolean;
  readOnly?: boolean;
  customColumns?: string[] | readonly string[];
  colWidth?: number;
  fetchMatrixData?: fetchMatrixFn;
  isImportDisabled?: boolean;
}

function Matrix({
  url,
  title = "global.timeSeries",
  customRowHeaders = [],
  enableDateTimeColumn = true,
  enableTimeSeriesColumns = true,
  aggregateColumns = false,
  rowHeaders = customRowHeaders.length > 0,
  showPercent = false,
  readOnly = false,
  customColumns,
  colWidth,
  fetchMatrixData,
  isImportDisabled = false,
}: MatrixProps) {
  const { t } = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [openImportDialog, setOpenImportDialog] = useState(false);

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
    handleImport,
    handleSaveUpdates,
    pendingUpdatesCount,
    undo,
    redo,
    canUndo,
    canRedo,
  } = useMatrix(
    study.id,
    url,
    enableDateTimeColumn,
    enableTimeSeriesColumns,
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

  if (!data[0]?.length) {
    return <EmptyView title={t("matrix.message.matrixEmpty")} />;
  }

  return (
    <MatrixContainer>
      <MatrixHeader>
        <MatrixTitle>{t(title)}</MatrixTitle>
        <MatrixActions
          onImport={() => setOpenImportDialog(true)}
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
          isImportDisabled={isImportDisabled}
        />
      </MatrixHeader>
      <Divider sx={{ width: 1, mt: 1, mb: 2 }} />
      <MatrixGrid
        data={data}
        aggregates={aggregates}
        columns={columns}
        rows={data.length}
        rowHeaders={customRowHeaders}
        dateTime={dateTime}
        onCellEdit={handleCellEdit}
        onMultipleCellsEdit={handleMultipleCellsEdit}
        isReadOnly={isSubmitting || readOnly}
        isPercentDisplayEnabled={showPercent}
      />
      {openImportDialog && (
        <ImportDialog
          open={openImportDialog}
          title={t("matrix.importNewMatrix")}
          dropzoneText={t("matrix.message.importHint")}
          onCancel={() => setOpenImportDialog(false)}
          onImport={handleImport}
          accept={{ "text/*": [".csv", ".tsv", ".txt"] }}
        />
      )}
    </MatrixContainer>
  );
}

export default Matrix;
