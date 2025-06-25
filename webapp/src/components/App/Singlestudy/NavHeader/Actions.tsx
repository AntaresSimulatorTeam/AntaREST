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

import CustomScrollbar from "@/components/common/CustomScrollbar";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { unarchiveStudy } from "@/services/api/study";
import { type StudyMetadata } from "@/types/types";
import { toError } from "@/utils/fnUtils";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import HistoryOutlinedIcon from "@mui/icons-material/HistoryOutlined";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import UnarchiveOutlinedIcon from "@mui/icons-material/UnarchiveOutlined";
import { Box, Button, Chip, Divider, IconButton, Tooltip, Typography } from "@mui/material";
import { enqueueSnackbar } from "notistack";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import FavoriteStudyToggle from "../../shared/studies/FavoriteStudyToggle";
import StudyActionsMenu from "../../shared/studies/StudyActionsMenu";
import CommandsDrawer from "../CommandsDrawer";

export type DialogType = "commands";

interface Props {
  study: StudyMetadata;
  parentStudy?: StudyMetadata;
  variantNb: number;
  isExplorer?: boolean;
}

function Actions({ study, parentStudy, variantNb, isExplorer }: Props) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [openDialog, setOpenDialog] = useState<DialogType | null>(null);

  const isManaged = study.managed;
  const isArchived = study.archived;
  const isVariant = study.type === "variantstudy";

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
        <Button onClick={handleClickBack} startIcon={<ArrowBackIcon />} color="secondary">
          {isExplorer ? t("button.back") : t("global.studies")}
        </Button>
        <Divider flexItem orientation="vertical" />
        <Box sx={{ flex: 1, overflow: "auto" }}>
          <CustomScrollbar>
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, flexWrap: "nowrap" }}>
              <Tooltip title={study.name} placement="bottom-start">
                <Typography
                  variant="h6"
                  noWrap
                  sx={{
                    flex: 1,
                    minWidth: 50,
                  }}
                >
                  {study.name}
                </Typography>
              </Tooltip>
              <FavoriteStudyToggle studyId={study.id} />
              <Tooltip title={t("study.copyId")}>
                <IconButton onClick={handleCopyId}>
                  <ContentCopyIcon />
                </IconButton>
              </Tooltip>
              {isManaged ? (
                <Chip label={t("study.managedStudy")} color="info" />
              ) : (
                <Chip label={study.workspace} />
              )}
              {study.tags?.map((tag) => <Chip key={tag} label={tag} />)}
            </Box>
          </CustomScrollbar>
        </Box>
        <Divider flexItem orientation="vertical" />
        {isVariant && (
          <IconButton color="primary" onClick={() => setOpenDialog("commands")}>
            <HistoryOutlinedIcon />
          </IconButton>
        )}
        {isExplorer && isArchived && (
          <Button
            onClick={handleUnarchive}
            startIcon={<UnarchiveOutlinedIcon />}
            variant="contained"
          >
            {t("global.unarchive")}
          </Button>
        )}
        <Button
          variant="outlined"
          onClick={(event) => setAnchorEl(event.currentTarget)}
          sx={{ px: 0 }}
        >
          <MoreVertIcon />
        </Button>
      </Box>
      <StudyActionsMenu
        open={!!anchorEl}
        anchorEl={anchorEl}
        study={study}
        parentStudy={parentStudy}
        variantNb={variantNb}
        onClose={() => setAnchorEl(null)}
      />
      <CommandsDrawer open={openDialog === "commands"} studyId={study.id} onClose={closeDialog} />
    </>
  );
}

export default Actions;
