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

import { Box, Divider, IconButton, Tooltip } from "@mui/material";
import SplitButton, { type SplitButtonProps } from "@/components/common/buttons/SplitButton";
import DownloadMatrixButton from "@/components/common/buttons/DownloadMatrixButton";
import UndoIcon from "@mui/icons-material/Undo";
import RedoIcon from "@mui/icons-material/Redo";
import FileDownloadIcon from "@mui/icons-material/FileDownload";
import SaveIcon from "@mui/icons-material/Save";
import { useTranslation } from "react-i18next";
import { LoadingButton } from "@mui/lab";

interface MatrixActionsProps {
  onImport: SplitButtonProps["onClick"];
  onSave: VoidFunction;
  studyId: string;
  path: string;
  disabled: boolean;
  pendingUpdatesCount: number;
  isSubmitting: boolean;
  undo: VoidFunction;
  redo: VoidFunction;
  canUndo: boolean;
  canRedo: boolean;
  canImport?: boolean;
}

function MatrixActions({
  onImport,
  onSave,
  studyId,
  path,
  disabled,
  pendingUpdatesCount,
  isSubmitting,
  undo,
  redo,
  canUndo,
  canRedo,
  canImport = false,
}: MatrixActionsProps) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
      <Tooltip title={t("global.undo")}>
        <span>
          <IconButton onClick={undo} disabled={!canUndo} size="small" color="primary">
            <UndoIcon fontSize="small" />
          </IconButton>
        </span>
      </Tooltip>
      <Tooltip title={t("global.redo")}>
        <span>
          <IconButton onClick={redo} disabled={!canRedo} size="small" color="primary">
            <RedoIcon fontSize="small" />
          </IconButton>
        </span>
      </Tooltip>
      <LoadingButton
        onClick={onSave}
        loading={isSubmitting}
        loadingPosition="start"
        startIcon={<SaveIcon />}
        variant="contained"
        size="small"
        disabled={pendingUpdatesCount === 0}
      >
        ({pendingUpdatesCount})
      </LoadingButton>
      <Divider sx={{ mx: 2 }} orientation="vertical" flexItem />
      <SplitButton
        options={[t("global.import.fromFile"), t("global.import.fromDatabase")]}
        onClick={onImport}
        size="small"
        ButtonProps={{
          startIcon: <FileDownloadIcon />,
        }}
        disabled={isSubmitting || canImport}
      >
        {t("global.import")}
      </SplitButton>
      <DownloadMatrixButton studyId={studyId} path={path} disabled={disabled || isSubmitting} />
    </Box>
  );
}

export default MatrixActions;
