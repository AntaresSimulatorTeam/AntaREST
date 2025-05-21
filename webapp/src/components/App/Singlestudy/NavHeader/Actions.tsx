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

import { type StudyMetadata } from "@/types/types";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
// import HistoryOutlinedIcon from "@mui/icons-material/HistoryOutlined";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { unarchiveStudy } from "@/services/api/study";
import { toError } from "@/utils/fnUtils";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import { Box, Button, Chip, Divider, Tooltip, Typography } from "@mui/material";
import { enqueueSnackbar } from "notistack";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import FavoriteStudyToggle from "../../../common/studies/FavoriteStudyToggle";
import StudyActionsMenu from "../../shared/studies/StudyActionsMenu";

export type DialogType = "launch" | "upgrade" | "move" | "properties" | "export" | "delete";

interface Props {
  study: StudyMetadata;
  parentStudy?: StudyMetadata;
  hasVariants: boolean;
  isExplorer?: boolean;
}

function Actions({ study, parentStudy, hasVariants, isExplorer }: Props) {
  const [t] = useTranslation();
  const navigate = useNavigate();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [openDialog, setOpenDialog] = useState<DialogType | null>(null);
  const isManaged = study.managed;
  const isArchived = study.archived;

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const closeDialog = () => setOpenDialog(null);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleClickBack = () => {
    if (isExplorer) {
      navigate(`/studies/${study.id}`);
    } else {
      navigate("/studies");
    }
  };

  const handleCopyId = async () => {
    try {
      await navigator.clipboard.writeText(study.id);
      enqueueSnackbar(t("study.success.studyIdCopy"), {
        variant: "success",
      });
    } catch (err) {
      enqueueErrorSnackbar(t("study.error.studyIdCopy"), toError(err));
    }
  };

  const handleUnarchive = async () => {
    try {
      await unarchiveStudy(study.id);
    } catch (err) {
      enqueueErrorSnackbar(t("studies.error.unarchive", { studyname: study.name }), toError(err));
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Box
        sx={{
          width: 1,
          display: "flex",
          flexDirection: "row",
          justifyContent: "flex-start",
          alignItems: "center",
          boxSizing: "border-box",
          gap: 2,
        }}
      >
        <Box>
          <Button variant="text" color="secondary" onClick={handleClickBack} sx={{ p: 0 }}>
            <ArrowBackIcon
              color="secondary"
              onClick={handleClickBack}
              sx={{ cursor: "pointer", mr: 1 }}
            />
            <Tooltip title={isExplorer ? study.name : t("global.studies")} followCursor>
              <Typography variant="button">
                {isExplorer ? t("button.back") : t("global.studies")}
              </Typography>
            </Tooltip>
          </Button>
        </Box>
        <Divider flexItem orientation="vertical" />
        <Tooltip title={study.folder} placement="bottom-start">
          <Typography
            variant="h6"
            noWrap
            sx={{
              flex: 1,
            }}
          >
            {study.name}
          </Typography>
        </Tooltip>
        <FavoriteStudyToggle studyId={study.id} />
        <Tooltip title={t("study.copyId")}>
          <ContentCopyIcon
            sx={{
              cursor: "pointer",
              width: 16,
              height: 16,
              color: "text.secondary",
              "&:hover": { color: "primary.main" },
            }}
            onClick={handleCopyId}
          />
        </Tooltip>
        {isManaged ? (
          <Chip label={t("study.managedStudy")} color="info" />
        ) : (
          <Chip label={study.workspace} />
        )}
        {study.tags?.map((tag) => <Chip key={tag} label={tag} />)}
        {isExplorer && (
          <Button
            variant="contained"
            onClick={() => (isArchived ? handleUnarchive() : setOpenDialog("launch"))}
          >
            {isArchived ? t("global.unarchive") : t("global.launch")}
          </Button>
        )}
        <Divider flexItem orientation="vertical" />
        {/* {study.type === StudyType.VARIANT && (
          <Button variant="outlined" onClick={onOpenCommands} sx={{ minWidth: 0 }}>
            <HistoryOutlinedIcon />
          </Button>
        )} */}
        <Button
          variant="outlined"
          color="primary"
          sx={{ width: "auto", minWidth: 0, px: 0 }}
          onClick={(event) => setAnchorEl(event.currentTarget)}
        >
          <MoreVertIcon />
        </Button>
      </Box>
      <StudyActionsMenu
        open={!!anchorEl}
        anchorEl={anchorEl}
        study={study}
        parentStudy={parentStudy}
        hasVariants={hasVariants}
        onClose={() => setAnchorEl(null)}
      />
      {/*  {openLauncherDialog && (
        <LauncherDialog
          open={openLauncherDialog}
          studyIds={[study.id]}
          onClose={() => setOpenLauncherDialog(false)}
        />
      )}

      {openUpgradeDialog && (
        <UpgradeDialog
          study={study}
          open={openUpgradeDialog}
          onClose={() => setOpenUpgradeDialog(false)}
        />
      )}
      {openExportDialog && (
        <ExportDialog
          open={openExportDialog}
          onClose={() => setOpenExportDialog(false)}
          study={study}
        />
      )} */}

      {/* {openCommands && studyId && (
        <CommandDrawer
          open={openCommands}
          studyId={studyId}
          onClose={() => setOpenCommands(false)}
        />
      )} */}
    </>
  );
}

export default Actions;
