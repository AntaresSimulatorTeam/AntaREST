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
import { archiveStudy, copyStudy, unarchiveStudy } from "@/services/api/study";
import { ListItemIcon, ListItemText, Menu, MenuItem, type MenuProps } from "@mui/material";
import ArchiveOutlinedIcon from "@mui/icons-material/ArchiveOutlined";
import UnarchiveOutlinedIcon from "@mui/icons-material/UnarchiveOutlined";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import DeleteOutlinedIcon from "@mui/icons-material/DeleteOutlined";
import BoltIcon from "@mui/icons-material/Bolt";
import FileCopyOutlinedIcon from "@mui/icons-material/FileCopyOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import DriveFileMoveIcon from "@mui/icons-material/DriveFileMove";
import debug from "debug";
import { useTranslation } from "react-i18next";
import type { StudyMetadata } from "@/types/types";
import type { DialogsType } from "./types";
import type { SvgIconComponent } from "@mui/icons-material";

const logError = debug("antares:studieslist:error");

interface Props {
  anchorEl: MenuProps["anchorEl"];
  onClose: VoidFunction;
  study: StudyMetadata;
  setStudyToLaunch: (id: StudyMetadata["id"]) => void;
  setOpenDialog: (type: DialogsType) => void;
}

function ActionsMenu(props: Props) {
  const { anchorEl, onClose, study, setStudyToLaunch, setOpenDialog } = props;
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  ////////////////////////////////////////////////////////////////
  // Events Handlers
  ////////////////////////////////////////////////////////////////

  const handleLaunchClick = () => {
    setStudyToLaunch(study.id);
    onClose();
  };

  const handleUnarchiveClick = () => {
    unarchiveStudy(study.id).catch((err) => {
      enqueueErrorSnackbar(t("studies.error.unarchive", { studyname: study.name }), err);
      logError("Failed to unarchive study", study, err);
    });

    onClose();
  };

  const handleArchiveClick = () => {
    archiveStudy(study.id).catch((err) => {
      enqueueErrorSnackbar(t("studies.error.archive", { studyname: study.name }), err);
      logError("Failed to archive study", study, err);
    });

    onClose();
  };

  const handleCopyClick = () => {
    copyStudy(study.id, `${study.name} (${t("studies.copySuffix")})`, false).catch((err) => {
      enqueueErrorSnackbar(t("studies.error.copyStudy"), err);
      logError("Failed to copy study", study, err);
    });

    onClose();
  };

  const handleMoveClick = () => {
    setOpenDialog("move");
    onClose();
  };

  const handlePropertiesClick = () => {
    setOpenDialog("properties");
    onClose();
  };

  const handleExportClick = () => {
    setOpenDialog("export");
    onClose();
  };

  const handleDeleteClick = () => {
    setOpenDialog("delete");
    onClose();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  const menuItem = (
    show: boolean,
    text: string,
    Icon: SvgIconComponent,
    onClick: VoidFunction,
    color?: string,
  ) =>
    show && (
      <MenuItem key={text} onClick={onClick}>
        <ListItemIcon sx={{ color }}>
          <Icon />
        </ListItemIcon>
        <ListItemText sx={{ color }}>{text}</ListItemText>
      </MenuItem>
    );

  return (
    <Menu open={!!anchorEl} anchorEl={anchorEl} keepMounted onClose={onClose}>
      {[
        menuItem(!study.archived, t("global.launch"), BoltIcon, handleLaunchClick),
        menuItem(!study.archived, t("study.properties"), EditOutlinedIcon, handlePropertiesClick),
        menuItem(!study.archived, t("global.copy"), FileCopyOutlinedIcon, handleCopyClick),
        menuItem(study.managed, t("studies.moveStudy"), DriveFileMoveIcon, handleMoveClick),
        menuItem(!study.archived, t("global.export"), DownloadOutlinedIcon, handleExportClick),
        menuItem(
          study.archived,
          t("global.unarchive"),
          UnarchiveOutlinedIcon,
          handleUnarchiveClick,
        ),
        menuItem(
          study.managed && !study.archived,
          t("global.archive"),
          ArchiveOutlinedIcon,
          handleArchiveClick,
        ),
        menuItem(
          study.managed,
          t("global.delete"),
          DeleteOutlinedIcon,
          handleDeleteClick,
          "error.light",
        ),
      ]}
    </Menu>
  );
}

export default ActionsMenu;
