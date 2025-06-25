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

import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getLatestStudyVersion } from "@/redux/selectors";
import { archiveStudy, unarchiveStudy } from "@/services/api/study";
import type { StudyMetadata } from "@/types/types";
import { toError } from "@/utils/fnUtils";
import { type SvgIconComponent } from "@mui/icons-material";
import ArchiveOutlinedIcon from "@mui/icons-material/ArchiveOutlined";
import BoltIcon from "@mui/icons-material/Bolt";
import DeleteOutlinedIcon from "@mui/icons-material/DeleteOutlined";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import DriveFileMoveIcon from "@mui/icons-material/DriveFileMove";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import FileCopyOutlinedIcon from "@mui/icons-material/FileCopyOutlined";
import SaveAsIcon from "@mui/icons-material/SaveAs";
import UnarchiveOutlinedIcon from "@mui/icons-material/UnarchiveOutlined";
import UpgradeIcon from "@mui/icons-material/Upgrade";
import { ListItemIcon, ListItemText, Menu, MenuItem, type MenuProps } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import CopyStudyDialog from "./dialogs/CopyStudyDialog";
import DeleteStudyDialog from "./dialogs/DeleteStudyDialog";
import ExportModal from "./dialogs/ExportModal";
import LaunchStudyDialog from "./dialogs/LaunchStudyDialog";
import MoveStudyDialog from "./dialogs/MoveStudyDialog";
import UpdateStudyDialog from "./dialogs/UpdateStudyDialog";
import UpgradeStudyDialog from "./dialogs/UpgradeStudyDialog";

export type DialogType =
  | "launch"
  | "properties"
  | "upgrade"
  | "export"
  | "move"
  | "copy"
  | "delete";

interface Props {
  open: boolean;
  anchorEl: MenuProps["anchorEl"];
  onClose: VoidFunction;
  study: StudyMetadata;
  parentStudy?: StudyMetadata;
  variantNb?: number;
}

function StudyActionsMenu({ open, anchorEl, onClose, study, parentStudy, variantNb }: Props) {
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [openDialog, setOpenDialog] = useState<DialogType | null>(null);
  const latestVersion = useAppSelector(getLatestStudyVersion);

  const isLatestVersion = study.version === latestVersion;
  const isVariant = study.type === "variantstudy";
  const isManaged = study.managed;
  const isArchived = study.archived;

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const closeDialog = () => setOpenDialog(null);

  ////////////////////////////////////////////////////////////////
  // Events Handlers
  ////////////////////////////////////////////////////////////////

  const handleDialog = (dialogType: DialogType) => () => {
    setOpenDialog(dialogType);
    onClose();
  };

  const handleArchive = () => {
    archiveStudy(study.id).catch((err) => {
      enqueueErrorSnackbar(t("studies.error.archive", { studyname: study.name }), toError(err));
    });

    onClose();
  };

  const handleUnarchive = () => {
    unarchiveStudy(study.id).catch((err) => {
      enqueueErrorSnackbar(t("studies.error.unarchive", { studyname: study.name }), toError(err));
    });

    onClose();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  const menuItem = (
    show: boolean,
    text: string,
    Icon: SvgIconComponent,
    onClick: DialogType | VoidFunction,
    color?: string,
  ) =>
    show && (
      <MenuItem key={text} onClick={typeof onClick === "string" ? handleDialog(onClick) : onClick}>
        <ListItemIcon sx={{ color }}>
          <Icon />
        </ListItemIcon>
        <ListItemText sx={{ color }}>{text}</ListItemText>
      </MenuItem>
    );

  return (
    <>
      <Menu open={open} anchorEl={anchorEl} keepMounted onClose={onClose}>
        {[
          menuItem(!isArchived, t("global.launch"), BoltIcon, "launch"),
          menuItem(!isArchived, t("study.properties"), EditOutlinedIcon, "properties"),
          menuItem(
            !isArchived && !isLatestVersion && !isVariant, // Display an error if the study has a variant
            t("study.upgrade"),
            UpgradeIcon,
            "upgrade",
          ),
          menuItem(
            !isArchived,
            isVariant ? t("study.copyVariant") : t("global.copy"),
            isVariant ? SaveAsIcon : FileCopyOutlinedIcon,
            "copy",
          ),
          menuItem(isManaged, t("global.move"), DriveFileMoveIcon, "move"),
          menuItem(!isArchived, t("global.export"), DownloadOutlinedIcon, "export"),
          menuItem(isArchived, t("global.unarchive"), UnarchiveOutlinedIcon, handleUnarchive),
          menuItem(
            isManaged && !isArchived && !isVariant,
            t("global.archive"),
            ArchiveOutlinedIcon,
            handleArchive,
          ),
          menuItem(isManaged, t("global.delete"), DeleteOutlinedIcon, "delete", "error.light"),
        ]}
      </Menu>
      {/* Keep conditional rendering for dialogs and not use only `open` property, because API calls are made on mount */}
      {openDialog === "launch" && (
        <LaunchStudyDialog open studyIds={[study.id]} onClose={closeDialog} />
      )}
      {openDialog === "properties" && (
        <UpdateStudyDialog open study={study} onClose={closeDialog} />
      )}
      {openDialog === "upgrade" && <UpgradeStudyDialog open study={study} onClose={closeDialog} />}
      {openDialog === "export" && <ExportModal open study={study} onClose={closeDialog} />}
      {openDialog === "move" && <MoveStudyDialog open study={study} onClose={closeDialog} />}
      {openDialog === "copy" && <CopyStudyDialog open study={study} onClose={closeDialog} />}
      {openDialog === "delete" && (
        <DeleteStudyDialog
          open
          study={study}
          parentStudy={parentStudy}
          variantNb={variantNb}
          onClose={closeDialog}
        />
      )}
    </>
  );
}

export default StudyActionsMenu;
