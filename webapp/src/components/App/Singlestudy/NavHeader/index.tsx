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

import { useState } from "react";
import debug from "debug";
import { useSnackbar } from "notistack";
import { useNavigate } from "react-router-dom";
import type { AxiosError } from "axios";
import { Box, Typography } from "@mui/material";
import UpgradeIcon from "@mui/icons-material/Upgrade";
import UnarchiveOutlinedIcon from "@mui/icons-material/UnarchiveOutlined";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import ArchiveOutlinedIcon from "@mui/icons-material/ArchiveOutlined";
import DeleteOutlinedIcon from "@mui/icons-material/DeleteOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import { useTranslation } from "react-i18next";
import type { StudyMetadata, VariantTree } from "../../../../types/types";
import { archiveStudy, unarchiveStudy } from "../../../../services/api/study";
import { deleteStudy } from "../../../../redux/ducks/studies";
import LauncherDialog from "../../Studies/LauncherDialog";
import PropertiesDialog from "../PropertiesDialog";
import useEnqueueErrorSnackbar from "../../../../hooks/useEnqueueErrorSnackbar";
import { getLatestStudyVersion } from "../../../../redux/selectors";
import ExportDialog from "../../Studies/ExportModal";
import ConfirmationDialog from "../../../common/dialogs/ConfirmationDialog";
import useAppSelector from "../../../../redux/hooks/useAppSelector";
import useAppDispatch from "../../../../redux/hooks/useAppDispatch";
import CheckBoxFE from "../../../common/fieldEditors/CheckBoxFE";
import Details from "./Details";
import Actions from "./Actions";
import UpgradeDialog from "../UpgradeDialog";
import ActionsMenu, { type ActionsMenuItem } from "./ActionsMenu";

const logError = debug("antares:singlestudy:navheader:error");

interface Props {
  study: StudyMetadata | undefined;
  parent: StudyMetadata | undefined;
  childrenTree: VariantTree | undefined;
  isExplorer?: boolean;
  openCommands: VoidFunction;
  updateStudyData: VoidFunction;
}

function NavHeader({
  study,
  parent,
  childrenTree,
  isExplorer,
  openCommands,
  updateStudyData,
}: Props) {
  const [t] = useTranslation();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const latestVersion = useAppSelector(getLatestStudyVersion);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [openLauncherDialog, setOpenLauncherDialog] = useState(false);
  const [openPropertiesDialog, setOpenPropertiesDialog] = useState(false);
  const [openUpgradeDialog, setOpenUpgradeDialog] = useState(false);
  const [deleteChildren, setDeleteChildren] = useState(false);
  const [openDeleteDialog, setOpenDeleteDialog] = useState(false);
  const [openExportDialog, setOpenExportDialog] = useState(false);
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const isLatestVersion = study?.version === latestVersion;
  const isManaged = !!study?.managed;
  const isArchived = !!study?.archived;
  const isVariant = study?.type === "variantstudy";
  const hasChildren = childrenTree && childrenTree.children.length > 0;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleOpenMenu = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLaunch = () => {
    setOpenLauncherDialog(true);
  };

  const handleArchive = async () => {
    if (study) {
      try {
        await archiveStudy(study.id);
      } catch (e) {
        enqueueErrorSnackbar(
          t("studies.error.archive", { studyname: study.name }),
          e as AxiosError,
        );
      } finally {
        handleClose();
      }
    }
  };

  const handleUnarchive = async () => {
    if (study) {
      try {
        await unarchiveStudy(study.id);
      } catch (e) {
        enqueueErrorSnackbar(
          t("studies.error.unarchive", { studyname: study.name }),
          e as AxiosError,
        );
      } finally {
        handleClose();
      }
    }
  };

  const handleDelete = async () => {
    if (study) {
      try {
        await dispatch(deleteStudy({ id: study.id, deleteChildren })).unwrap();
        navigate(parent ? `/studies/${parent?.id}` : "/studies");
      } catch (err) {
        enqueueErrorSnackbar(t("studies.error.deleteStudy"), err as AxiosError);
        logError("Failed to delete study", study, err);
      } finally {
        setDeleteChildren(false);
        setOpenDeleteDialog(false);
      }
    }
  };

  const handleCopyId = async () => {
    if (study) {
      try {
        await navigator.clipboard.writeText(study.id);
        enqueueSnackbar(t("study.success.studyIdCopy"), {
          variant: "success",
        });
      } catch (e) {
        enqueueErrorSnackbar(t("study.error.studyIdCopy"), e as AxiosError);
      }
    }
  };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const menuItems: ActionsMenuItem[] = [
    {
      key: "study.properties",
      icon: EditOutlinedIcon,
      action: () => setOpenPropertiesDialog(true),
      condition: !isArchived,
    },
    {
      key: "study.upgrade",
      icon: UpgradeIcon,
      action: () => setOpenUpgradeDialog(true),
      condition: !isArchived && !isLatestVersion && !isVariant && !hasChildren,
    },
    {
      key: "global.export",
      icon: DownloadOutlinedIcon,
      action: () => setOpenExportDialog(true),
      condition: !isArchived,
    },
    {
      key: "global.archive",
      icon: ArchiveOutlinedIcon,
      action: handleArchive,
      condition: !isArchived && isManaged,
    },
    {
      key: "global.unarchive",
      icon: UnarchiveOutlinedIcon,
      action: handleUnarchive,
      condition: isArchived,
    },
    {
      key: "global.delete",
      icon: DeleteOutlinedIcon,
      action: () => setOpenDeleteDialog(true),
      color: "error.light",
      condition: isManaged,
    },
  ];

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        width: 1,
        py: 1,
        px: 2,
        overflow: "hidden",
        gap: 1,
      }}
    >
      <Box
        sx={{
          width: 1,
          display: "flex",
        }}
      >
        <Actions
          study={study}
          onOpenCommands={openCommands}
          isExplorer={isExplorer}
          onCopyId={handleCopyId}
          onLaunch={handleLaunch}
          onUnarchive={handleUnarchive}
          onOpenMenu={handleOpenMenu}
        />
        <ActionsMenu
          anchorEl={anchorEl}
          open={!!anchorEl}
          onClose={handleClose}
          items={menuItems}
        />
      </Box>
      <Details study={study} parent={parent} childrenTree={childrenTree} />
      {study && openLauncherDialog && (
        <LauncherDialog
          open={openLauncherDialog}
          studyIds={[study.id]}
          onClose={() => setOpenLauncherDialog(false)}
        />
      )}
      {study && openPropertiesDialog && (
        <PropertiesDialog
          open={openPropertiesDialog}
          onClose={() => setOpenPropertiesDialog(false)}
          study={study}
          updateStudyData={updateStudyData}
        />
      )}
      {openDeleteDialog && (
        <ConfirmationDialog
          title={t("dialog.title.confirmation")}
          onCancel={() => setOpenDeleteDialog(false)}
          onConfirm={handleDelete}
          alert="warning"
          open
        >
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              alignItems: "flex-start",
              width: 1,
              height: "auto",
              gap: 1,
            }}
          >
            <Typography>{t("studies.question.delete")}</Typography>
            <CheckBoxFE
              value={deleteChildren}
              label={t("studies.deleteSubvariants")}
              onChange={(_, checked) => setDeleteChildren(checked)}
            />
          </Box>
        </ConfirmationDialog>
      )}
      {study && openUpgradeDialog && (
        <UpgradeDialog
          study={study}
          open={openUpgradeDialog}
          onClose={() => setOpenUpgradeDialog(false)}
        />
      )}
      {study && openExportDialog && (
        <ExportDialog
          open={openExportDialog}
          onClose={() => setOpenExportDialog(false)}
          study={study}
        />
      )}
    </Box>
  );
}

export default NavHeader;
