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

import { Box, Tooltip, Typography, Chip, Button, Divider } from "@mui/material";
import HistoryOutlinedIcon from "@mui/icons-material/HistoryOutlined";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { StudyType, type StudyMetadata } from "@/types/types";
import FavoriteStudyToggle from "../../../common/studies/FavoriteStudyToggle";

interface Props {
  study: StudyMetadata | undefined;
  isExplorer: boolean | undefined;
  onCopyId: () => Promise<void>;
  onUnarchive: () => Promise<void>;
  onLaunch: VoidFunction;
  onOpenCommands: VoidFunction;
  onOpenMenu: React.MouseEventHandler;
}

function Actions({
  study,
  isExplorer,
  onCopyId,
  onUnarchive,
  onLaunch,
  onOpenCommands,
  onOpenMenu,
}: Props) {
  const [t] = useTranslation();
  const navigate = useNavigate();
  const isManaged = study?.managed;
  const isArchived = study?.archived;

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleClickBack = () => {
    if (isExplorer) {
      navigate(`/studies/${study?.id}`);
    } else {
      navigate("/studies");
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (!study) {
    return null;
  }

  return (
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
          <Tooltip title={isExplorer ? study?.name : t("global.studies")} followCursor>
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
          onClick={onCopyId}
        />
      </Tooltip>
      {isManaged ? (
        <Chip label={t("study.managedStudy")} color="info" />
      ) : (
        <Chip label={study.workspace} />
      )}
      {study.tags?.map((tag) => <Chip key={tag} label={tag} />)}
      {isExplorer && (
        <Button variant="contained" onClick={isArchived ? onUnarchive : onLaunch}>
          {isArchived ? t("global.unarchive") : t("global.launch")}
        </Button>
      )}
      <Divider flexItem orientation="vertical" />
      {study.type === StudyType.VARIANT && (
        <Button variant="outlined" onClick={onOpenCommands} sx={{ minWidth: 0 }}>
          <HistoryOutlinedIcon />
        </Button>
      )}
      <Button
        variant="outlined"
        color="primary"
        sx={{ width: "auto", minWidth: 0, px: 0 }}
        onClick={onOpenMenu}
      >
        <MoreVertIcon />
      </Button>
    </Box>
  );
}

export default Actions;
