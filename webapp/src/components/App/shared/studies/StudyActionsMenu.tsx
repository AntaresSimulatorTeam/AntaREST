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

import ConfirmationDialog from "@/components/common/dialogs/ConfirmationDialog";
import useConfirm from "@/hooks/useConfirm";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { deleteStudy } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getLatestStudyVersion } from "@/redux/selectors";
import { archiveStudy, unarchiveStudy } from "@/services/api/study";
import type { StudyMetadata } from "@/types/types";
import { toError } from "@/utils/fnUtils";
import type { SvgIconComponent } from "@mui/icons-material";
import ArchiveOutlinedIcon from "@mui/icons-material/ArchiveOutlined";
import BoltIcon from "@mui/icons-material/Bolt";
import DeleteOutlinedIcon from "@mui/icons-material/DeleteOutlined";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import DriveFileMoveIcon from "@mui/icons-material/DriveFileMove";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import FileCopyOutlinedIcon from "@mui/icons-material/FileCopyOutlined";
import UnarchiveOutlinedIcon from "@mui/icons-material/UnarchiveOutlined";
import UpgradeIcon from "@mui/icons-material/Upgrade";
import { ListItemIcon, ListItemText, Menu, MenuItem, type MenuProps } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import CopyStudyDialog from "./dialogs/CopyStudyDialog";
import ExportModal from "./dialogs/ExportModal";
import LauncherDialog from "./dialogs/LauncherDialog";
import MoveStudyDialog from "./dialogs/MoveStudyDialog";
import PropertiesDialog from "./dialogs/PropertiesDialog";
import UpgradeDialog from "./dialogs/UpgradeDialog";

export type DialogType = "launch" | "properties" | "upgrade" | "export" | "move" | "copy";

interface Props {
  open: boolean;
  anchorEl: MenuProps["anchorEl"];
  onClose: VoidFunction;
  study: StudyMetadata;
  parentStudy?: StudyMetadata;
}

function StudyActionsMenu({ open, anchorEl, onClose, study, parentStudy }: Props) {
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [openDialog, setOpenDialog] = useState<DialogType | null>(null);
  const deleteAction = useConfirm();
  const latestVersion = useAppSelector(getLatestStudyVersion);
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

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

  const handleDeleteClick = () => {
    deleteAction.showConfirm().then((confirm) => {
      if (confirm) {
        dispatch(deleteStudy({ id: study.id, deleteChildren: true }))
          .unwrap()
          .then(() => {
            navigate(parentStudy ? `/studies/${parentStudy.id}` : "/studies");
          })
          .catch((err) => {
            enqueueErrorSnackbar(t("studies.error.deleteStudy"), toError(err));
          });
      }
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
            FileCopyOutlinedIcon,
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
          menuItem(
            isManaged,
            t("global.delete"),
            DeleteOutlinedIcon,
            handleDeleteClick,
            "error.light",
          ),
        ]}
      </Menu>
      {/* Keep conditional rendering for dialogs and not use only `open` property, because API calls are made on mount */}
      {openDialog === "launch" && (
        <LauncherDialog open studyIds={[study.id]} onClose={closeDialog} />
      )}
      {openDialog === "properties" && <PropertiesDialog open study={study} onClose={closeDialog} />}
      {openDialog === "upgrade" && <UpgradeDialog open study={study} onClose={closeDialog} />}
      {openDialog === "export" && <ExportModal open study={study} onClose={closeDialog} />}
      {openDialog === "move" && <MoveStudyDialog open study={study} onClose={closeDialog} />}
      {openDialog === "copy" && <CopyStudyDialog open study={study} onClose={closeDialog} />}
      {/* Confirm deletion */}
      <ConfirmationDialog
        open={deleteAction.isPending}
        onConfirm={deleteAction.yes}
        onCancel={deleteAction.no}
        titleIcon={DeleteOutlinedIcon}
        alert="error"
        maxWidth="xs"
      >
        {t("studies.question.delete")}
      </ConfirmationDialog>
    </>
  );
}

export default StudyActionsMenu;
