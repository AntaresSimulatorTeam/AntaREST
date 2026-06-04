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

import useDialog from "@/hooks/useDialog";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudiesById } from "@/redux/selectors";
import LaunchStudiesDialog from "@/routes/-shared/components/studies/dialogs/LaunchStudiesDialog";
import MoveStudyDialog from "@/routes/-shared/components/studies/dialogs/MoveStudyDialog";
import type { Study } from "@/services/api/studies/types";
import BoltIcon from "@mui/icons-material/Bolt";
import CheckBoxIcon from "@mui/icons-material/CheckBox";
import DeleteIcon from "@mui/icons-material/Delete";
import DriveFileMoveIcon from "@mui/icons-material/DriveFileMove";
import { Button, IconButton, Stack, Tooltip, Typography, type ButtonProps } from "@mui/material";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import DeleteStudiesDialog from "./DeleteStudiesDialog";

interface Props {
  selectedStudyIds: Array<Study["id"]>;
  setSelectedStudyIds: (ids: Array<Study["id"]>) => void;
}

function BatchActions({ selectedStudyIds, setSelectedStudyIds }: Props) {
  const { t } = useTranslation();
  const { openDialog } = useDialog();
  const studiesById = useAppSelector(getStudiesById);

  const selection = useMemo(() => {
    const studies = selectedStudyIds.map((id) => studiesById[id]).filter(Boolean);

    return {
      all: studies,
      managed: studies.filter((s) => s.managed),
      unarchived: studies.filter((s) => !s.archived),
    };
  }, [selectedStudyIds, studiesById]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDeselectAll = () => {
    setSelectedStudyIds([]);
  };

  const handleLaunchStudies = () => {
    openDialog(({ onClose }) => (
      <LaunchStudiesDialog
        open
        studyIds={selection.unarchived.map((s) => s.id)}
        onClose={onClose}
        onRun={handleDeselectAll}
      />
    ));
  };

  const handleMoveStudies = () => {
    openDialog(({ onClose }) => (
      <MoveStudyDialog
        open
        studies={selection.managed}
        onClose={onClose}
        onRun={handleDeselectAll}
      />
    ));
  };

  const handleDeleteStudies = () => {
    openDialog(({ onClose }) => (
      <DeleteStudiesDialog
        open
        studyIds={selection.managed.map((s) => s.id)}
        onClose={onClose}
        onRun={handleDeselectAll}
      />
    ));
  };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const renderActionButton = (params: {
    defaultTooltip: string;
    partialSelectionTooltip: (options: { count: number; total: number }) => string;
    onClick: VoidFunction;
    color: ButtonProps["color"];
    icon: React.ReactNode;
    label: string;
    selectionCount: number;
  }) => {
    if (params.selectionCount === 0) {
      return null;
    }

    const isPartialSelection = params.selectionCount < selection.all.length;
    const tooltip = isPartialSelection
      ? params.partialSelectionTooltip({
          count: params.selectionCount,
          total: selection.all.length,
        })
      : params.defaultTooltip;

    return (
      <Tooltip title={tooltip}>
        <Button onClick={params.onClick} color={params.color} startIcon={params.icon}>
          {params.label}
          {isPartialSelection && (
            <Typography component="span" variant="caption" sx={{ ml: 0.5, opacity: 0.7 }}>
              ({params.selectionCount}/{selection.all.length})
            </Typography>
          )}
        </Button>
      </Tooltip>
    );
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (selection.all.length === 0) {
    return null;
  }

  return (
    <>
      {renderActionButton({
        defaultTooltip: t("global.launch"),
        partialSelectionTooltip: (options) => t("studies.launchOnlyUnarchivedStudies", options),
        onClick: handleLaunchStudies,
        color: "primary",
        icon: <BoltIcon />,
        label: t("global.launch"),
        selectionCount: selection.unarchived.length,
      })}
      {renderActionButton({
        defaultTooltip: t("global.move"),
        partialSelectionTooltip: (options) => t("studies.moveOnlyManagedStudies", options),
        onClick: handleMoveStudies,
        color: "inherit",
        icon: <DriveFileMoveIcon />,
        label: t("global.move"),
        selectionCount: selection.managed.length,
      })}
      {renderActionButton({
        defaultTooltip: t("global.delete"),
        partialSelectionTooltip: (options) => t("studies.deleteOnlyManagedStudies", options),
        onClick: handleDeleteStudies,
        color: "error",
        icon: <DeleteIcon />,
        label: t("global.delete"),
        selectionCount: selection.managed.length,
      })}
      <Tooltip title={t("studies.deselectAll")}>
        <Stack>
          <IconButton color="primary" onClick={handleDeselectAll}>
            <CheckBoxIcon />
          </IconButton>
          <Typography variant="body2">({selection.all.length})</Typography>
        </Stack>
      </Tooltip>
    </>
  );
}

export default BatchActions;
