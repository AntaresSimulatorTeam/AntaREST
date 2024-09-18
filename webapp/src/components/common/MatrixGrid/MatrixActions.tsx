/** Copyright (c) 2024, RTE (https://www.rte-france.com)
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
import SplitButton from "../buttons/SplitButton";
import DownloadMatrixButton from "../DownloadMatrixButton";
import FileDownload from "@mui/icons-material/FileDownload";
import { useTranslation } from "react-i18next";
import { LoadingButton } from "@mui/lab";
import Save from "@mui/icons-material/Save";
import { Undo, Redo } from "@mui/icons-material";

interface MatrixActionsProps {
  onImport: VoidFunction;
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
}: MatrixActionsProps) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
      <Tooltip title={t("global.undo")}>
        <span>
          <IconButton
            onClick={undo}
            disabled={!canUndo}
            size="small"
            color="primary"
          >
            <Undo fontSize="small" />
          </IconButton>
        </span>
      </Tooltip>
      <Tooltip title={t("global.redo")}>
        <span>
          <IconButton
            onClick={redo}
            disabled={!canRedo}
            size="small"
            color="primary"
          >
            <Redo fontSize="small" />
          </IconButton>
        </span>
      </Tooltip>
      <LoadingButton
        onClick={onSave}
        loading={isSubmitting}
        loadingPosition="start"
        startIcon={<Save />}
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
          startIcon: <FileDownload />,
        }}
        disabled={isSubmitting}
      >
        {t("global.import")}
      </SplitButton>
      <DownloadMatrixButton
        studyId={studyId}
        path={path}
        disabled={disabled || isSubmitting}
      />
    </Box>
  );
}

export default MatrixActions;
