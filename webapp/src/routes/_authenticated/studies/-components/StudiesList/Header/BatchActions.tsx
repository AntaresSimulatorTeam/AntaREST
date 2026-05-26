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
  /** Number of selected studies that are unarchived (and therefore launchable). */
  unarchivedCount: number;
  /** Number of selected studies that are managed (and therefore movable/deletable). */
  managedCount: number;
  /** If not provided, the Launch button is not rendered (only unarchived studies can be launched). */
  onLaunch?: () => void;
  /** If not provided, the Delete button is not rendered (only managed studies can be deleted). */
  onDelete?: () => void;
  onDeselectAll: () => void;
  /** If not provided, the Move button is not rendered (only managed studies can be moved). */
  onMove?: () => void;
}

function BatchActions({
  selectedCount,
  unarchivedCount,
  managedCount,
  onLaunch,
  onDelete,
  onDeselectAll,
  onMove,
}: BatchActionsProps) {
  const { t } = useTranslation();

  if (selectedCount === 0) {
    return null;
  }

  const isMixedArchiveState = unarchivedCount < selectedCount;
  const isMixedType = managedCount < selectedCount;

  const launchTooltip = isMixedArchiveState
    ? t("studies.launchOnlyUnarchivedStudies", { count: unarchivedCount, total: selectedCount })
    : t("global.launch");

  const moveTooltip = isMixedType
    ? t("studies.moveOnlyManagedStudies", { count: managedCount, total: selectedCount })
    : t("global.move");

  const deleteTooltip = isMixedType
    ? t("studies.deleteOnlyManagedStudies", { count: managedCount, total: selectedCount })
    : t("global.delete");

  return (
    <>
      {onLaunch && (
        <Tooltip title={launchTooltip}>
          <Button onClick={onLaunch} color="primary" startIcon={<BoltIcon />}>
            {t("global.launch")}
            {isMixedArchiveState && (
              <Typography component="span" variant="caption" sx={{ ml: 0.5, opacity: 0.7 }}>
                ({unarchivedCount}/{selectedCount})
              </Typography>
            )}
          </Button>
        </Tooltip>
      )}
      {onMove && (
        <Tooltip title={moveTooltip}>
          <Button onClick={onMove} color="inherit" startIcon={<DriveFileMoveIcon />}>
            {t("global.move")}
            {isMixedType && (
              <Typography component="span" variant="caption" sx={{ ml: 0.5, opacity: 0.7 }}>
                ({managedCount}/{selectedCount})
              </Typography>
            )}
          </Button>
        </Tooltip>
      )}
      {onDelete && (
        <Tooltip title={deleteTooltip}>
          <Button onClick={onDelete} color="error" startIcon={<DeleteIcon />}>
            {t("global.delete")}
            {isMixedType && (
              <Typography component="span" variant="caption" sx={{ ml: 0.5, opacity: 0.7 }}>
                ({managedCount}/{selectedCount})
              </Typography>
            )}
          </Button>
        </Tooltip>
      )}
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
