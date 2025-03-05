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

import { Box, Button, Divider, IconButton, Tooltip } from "@mui/material";
import SplitButton, { type SplitButtonProps } from "@/components/common/buttons/SplitButton";
import DownloadMatrixButton from "@/components/common/buttons/DownloadMatrixButton";
import UndoIcon from "@mui/icons-material/Undo";
import RedoIcon from "@mui/icons-material/Redo";
import FileUploadIcon from "@mui/icons-material/FileUpload";
import SaveIcon from "@mui/icons-material/Save";
import { useTranslation } from "react-i18next";
import MatrixResize from "../MatrixResize";
import { useMatrixContext } from "../../context/MatrixContext";

interface MatrixActionsProps {
  studyId: string;
  path: string;
  onImport: SplitButtonProps["onClick"];
  onSave: VoidFunction;
  disabled: boolean;
  isTimeSeries: boolean;
  onMatrixUpdated: VoidFunction;
  canImport?: boolean;
}

function MatrixActions({
  studyId,
  path,
  onImport,
  onSave,
  disabled,
  isTimeSeries,
  canImport = false,
}: MatrixActionsProps) {
  const { t } = useTranslation();
  const { isSubmitting, updateCount, undo, redo, canUndo, canRedo, isDirty } = useMatrixContext();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1, overflowX: "auto" }}>
      <Tooltip title={t("global.undo")}>
        <span>
          <IconButton onClick={undo} disabled={isSubmitting || !canUndo}>
            <UndoIcon fontSize="small" />
          </IconButton>
        </span>
      </Tooltip>
      <Tooltip title={t("global.redo")}>
        <span>
          <IconButton onClick={redo} disabled={isSubmitting || !canRedo}>
            <RedoIcon fontSize="small" />
          </IconButton>
        </span>
      </Tooltip>
      <Tooltip title={t("global.save")}>
        <Button
          role="button"
          aria-label={t("global.save")}
          onClick={onSave}
          loading={isSubmitting}
          loadingPosition="start"
          startIcon={<SaveIcon />}
          variant="contained"
          disabled={!isDirty}
        >
          ({updateCount})
        </Button>
      </Tooltip>
      <Divider sx={{ mx: 1 }} orientation="vertical" flexItem />
      {isTimeSeries && (
        <>
          <MatrixResize />
          <Divider sx={{ mx: 1 }} orientation="vertical" flexItem />
        </>
      )}

      <SplitButton
        options={[t("global.import.fromFile"), t("global.import.fromDatabase")]}
        onClick={onImport}
        ButtonProps={{
          startIcon: <FileUploadIcon />,
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
