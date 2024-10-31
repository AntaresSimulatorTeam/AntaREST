/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";

import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import HistoryOutlinedIcon from "@mui/icons-material/HistoryOutlined";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import { Box, Button, Chip, Divider, Tooltip, Typography } from "@mui/material";

import { StudyMetadata, StudyType } from "@/common/types";
import StarToggle from "@/components/common/StarToggle";
import { toggleFavorite } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { isCurrentStudyFavorite } from "@/redux/selectors";

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
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const isStudyFavorite = useAppSelector(isCurrentStudyFavorite);
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
        <Button
          variant="text"
          color="secondary"
          onClick={handleClickBack}
          sx={{ pl: 0 }}
        >
          <ArrowBackIcon
            color="secondary"
            onClick={handleClickBack}
            sx={{ cursor: "pointer", mr: 1 }}
          />
          <Tooltip
            title={isExplorer ? study?.name : t("global.studies")}
            followCursor
          >
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
            ml: 1,
          }}
        >
          {study.name}
        </Typography>
      </Tooltip>
      <StarToggle
        isActive={isStudyFavorite}
        activeTitle={t("studies.removeFavorite")}
        unactiveTitle={t("studies.addFavorite")}
        onToggle={() => dispatch(toggleFavorite(study.id))}
      />
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
        <Chip
          label={t("study.managedStudy")}
          variant="filled"
          color="info"
          size="small"
        />
      ) : (
        <Chip label={study.workspace} variant="filled" size="small" />
      )}
      {study.tags?.map((tag) => (
        <Chip key={tag} label={tag} variant="filled" size="small" />
      ))}
      {isExplorer && (
        <Button
          size="small"
          variant="contained"
          color="primary"
          onClick={isArchived ? onUnarchive : onLaunch}
        >
          {isArchived ? t("global.unarchive") : t("global.launch")}
        </Button>
      )}
      <Divider flexItem orientation="vertical" />
      {study.type === StudyType.VARIANT && (
        <Button
          size="small"
          variant="outlined"
          color="primary"
          onClick={onOpenCommands}
          sx={{ minWidth: 0 }}
        >
          <HistoryOutlinedIcon />
        </Button>
      )}
      <Button
        size="small"
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
