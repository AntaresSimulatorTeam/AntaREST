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
import MatrixGrid from ".";
import { useMatrix } from "./useMatrix";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import ImportDialog from "../dialogs/ImportDialog";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../common/types";
import { MatrixContainer, MatrixHeader, MatrixTitle } from "./style";
import MatrixActions from "./MatrixActions";
import EmptyView from "../page/SimpleContent";
import { fetchMatrixFn } from "../../App/Singlestudy/explore/Modelization/Areas/Hydro/utils";
import { AggregateConfig } from "./types";

interface MatrixProps {
  url: string;
  title?: string;
  customRowHeaders?: string[];
  enableDateTimeColumn?: boolean;
  enableTimeSeriesColumns?: boolean;
  aggregateColumns?: AggregateConfig;
  enableRowHeaders?: boolean;
  enablePercentDisplay?: boolean;
  enableReadOnly?: boolean;
  customColumns?: string[] | readonly string[];
  colWidth?: number;
  fetchMatrixData?: fetchMatrixFn;
}

function Matrix({
  url,
  title = "global.timeSeries",
  customRowHeaders = [],
  enableDateTimeColumn = true,
  enableTimeSeriesColumns = true,
  aggregateColumns = false,
  enableRowHeaders = customRowHeaders.length > 0,
  enablePercentDisplay = false,
  enableReadOnly = false,
  customColumns,
  colWidth,
  fetchMatrixData,
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
    enableRowHeaders,
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

  if (!data || data.length === 0) {
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
        isReaOnlyEnabled={isSubmitting || enableReadOnly}
        isPercentDisplayEnabled={enablePercentDisplay}
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
