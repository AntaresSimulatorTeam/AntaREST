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
import { Button, IconButton, Tooltip } from "@mui/material";
import { useTranslation } from "react-i18next";

interface BatchActionsProps {
  selectedCount: number;
  onLaunch: () => void;
  onDelete: () => void;
  onDeselectAll: () => void;
}

function BatchActions({ selectedCount, onLaunch, onDelete, onDeselectAll }: BatchActionsProps) {
  const { t } = useTranslation();

  if (selectedCount === 0) {
    return null;
  }

  return (
    <>
      <Tooltip title={t("studies.batchMode")}>
        <Button onClick={onLaunch} color="primary">
          <BoltIcon />
          {t("global.launch")} ({selectedCount})
        </Button>
      </Tooltip>
      <Tooltip title={t("global.delete")}>
        <Button onClick={onDelete} color="error">
          <DeleteIcon />
          {t("global.delete")} ({selectedCount})
        </Button>
      </Tooltip>
      <Tooltip title={t("studies.deselectAll")}>
        <IconButton color="primary" onClick={onDeselectAll}>
          <CheckBoxIcon />
        </IconButton>
      </Tooltip>
    </>
  );
}

export default BatchActions;
