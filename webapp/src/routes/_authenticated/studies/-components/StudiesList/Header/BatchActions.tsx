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

import BoltIcon from "@mui/icons-material/Bolt";
import CheckBoxIcon from "@mui/icons-material/CheckBox";
import DeleteIcon from "@mui/icons-material/Delete";
import DriveFileMoveIcon from "@mui/icons-material/DriveFileMove";
import { Button, IconButton, Stack, Tooltip, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

interface BatchActionsProps {
  selectedCount: number;
  onLaunch: () => void;
  onDelete: () => void;
  onDeselectAll: () => void;
  /** If not provided, the Move button is not rendered (only used for managed studies) */
  onMove?: () => void;
}

function BatchActions({
  selectedCount,
  onLaunch,
  onDelete,
  onDeselectAll,
  onMove,
}: BatchActionsProps) {
  const { t } = useTranslation();

  if (selectedCount === 0) {
    return null;
  }

  return (
    <>
      <Tooltip title={t("studies.batchMode")}>
        <Button onClick={onLaunch} color="primary" startIcon={<BoltIcon />}>
          {t("global.launch")}
        </Button>
      </Tooltip>
      {onMove && (
        <Tooltip title={t("global.move")}>
          <Button onClick={onMove} color="inherit" startIcon={<DriveFileMoveIcon />}>
            {t("global.move")}
          </Button>
        </Tooltip>
      )}
      <Tooltip title={t("global.delete")}>
        <Button onClick={onDelete} color="error" startIcon={<DeleteIcon />}>
          {t("global.delete")}
        </Button>
      </Tooltip>
      <Tooltip title={t("studies.deselectAll")}>
        <Stack>
          <IconButton color="primary" onClick={onDeselectAll}>
            <CheckBoxIcon />
          </IconButton>
          <Typography variant="body2">({selectedCount})</Typography>
        </Stack>
      </Tooltip>
    </>
  );
}

export default BatchActions;
