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

import CopyButton from "@/components/buttons/CopyButton";
import EditorIcon from "@/components/icons/EditorIcon";
import RouterButton from "@/components/router/RouterButton";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import useThemeColorScheme from "@/hooks/useThemeColorScheme";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudy } from "@/redux/selectors";
import { buildModificationDate, convertUTCToLocalTime } from "@/services/utils";
import { StudyType, type StudyMetadata } from "@/types/types";
import { toError } from "@/utils/fnUtils";
import { compactSemanticVersion } from "@/utils/versionUtils";
import AltRouteOutlinedIcon from "@mui/icons-material/AltRouteOutlined";
import ArchiveOutlinedIcon from "@mui/icons-material/ArchiveOutlined";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import ScheduleOutlinedIcon from "@mui/icons-material/ScheduleOutlined";
import UpdateOutlinedIcon from "@mui/icons-material/UpdateOutlined";
import {
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  Checkbox,
  Chip,
  colors,
  Divider,
  styled,
  Tooltip,
  Typography,
} from "@mui/material";
import { useNavigate } from "@tanstack/react-router";
import debug from "debug";
import { useSnackbar } from "notistack";
import { memo, useState } from "react";
import { useTranslation } from "react-i18next";
import { areEqual } from "react-window";
import FavoriteStudyToggle from "../../../../../-shared/components/studies/FavoriteStudyToggle";
import StudyActionsMenu from "../../../../../-shared/components/studies/StudyActionsMenu";

const logError = debug("antares:studieslist:error");

interface Props {
  id: StudyMetadata["id"];
  width: number;
  height: number;
  isSelected: boolean;
  hasStudiesSelected: boolean;
  toggleStudySelection: (id: StudyMetadata["id"]) => void;
}

const TinyText = styled(Typography)(({ theme }) => ({
  fontSize: "16px",
  color: theme.palette.text.secondary,
}));

const StudyCard = memo((props: Props) => {
  const { id, width, height, isSelected, hasStudiesSelected, toggleStudySelection } = props;
  const { t, i18n } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const study = useAppSelector((state) => getStudy(state, id));
  const navigate = useNavigate();
  const { isDarkMode } = useThemeColorScheme();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleMenuOpen = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleCopyId = () => {
    navigator.clipboard
      .writeText(id)
      .then(() => {
        enqueueSnackbar(t("study.success.studyIdCopy"), {
          variant: "success",
        });
      })
      .catch((err) => {
        enqueueErrorSnackbar(t("study.error.studyIdCopy"), toError(err));
        logError("Failed to copy id", study, err);
      });
  };

  const handleSelectionChange = () => {
    toggleStudySelection(id);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (!study) {
    return null;
  }

  return (
    <Card
      className="StudyCard"
      sx={{
        width,
        height,
        display: "flex",
        flexDirection: "column",
        position: "relative",
        outline: isSelected ? "1px solid" : "none",
        outlineColor: "primary.main",
      }}
      elevation={3}
    >
      <CardContent
        sx={{
          flexGrow: 1,
          display: "flex",
          flexDirection: "column",
          overflow: "auto",
          maxHeight: "calc(100% - 48px)",
        }}
      >
        <Box
          sx={{
            width: "100%",
            height: "36px",
            display: "flex",
            flexDirection: "row",
            justifyContent: "flex-start",
            px: 0.5,
          }}
        >
          <Tooltip title={study.name}>
            <Typography
              noWrap
              variant="h6"
              component="div"
              onClick={() => navigate({ to: "/studies/$studyId", params: { studyId: study.id } })}
              sx={{
                boxSizing: "border-box",
                flexFlow: "nowrap",
                width: "calc(100% - 64px)",
                whiteSpace: "nowrap",
                textOverflow: "ellipsis",
                overflow: "hidden",
                cursor: "pointer",
                "&:hover": {
                  color: "primary.main",
                  textDecoration: "underline",
                },
              }}
            >
              {study.name}
            </Typography>
          </Tooltip>
          <Box
            sx={{
              display: "flex",
              flexFlow: "row nowrap",
              justifyContent: "center",
              alignItems: "center",
              p: 0,
            }}
          >
            <Checkbox
              checked={isSelected}
              sx={[
                !hasStudiesSelected && {
                  ".StudyCard:not(:hover) &": {
                    display: "none",
                  },
                },
              ]}
              onChange={handleSelectionChange}
            />
            <FavoriteStudyToggle studyId={study.id} />
            <CopyButton tooltip={t("study.copyId")} onClick={handleCopyId} />
          </Box>
        </Box>
        <Tooltip title={study.folder || ""}>
          <Typography
            variant="caption"
            component="div"
            sx={{
              boxSizing: "border-box",
              flexFlow: "nowrap",
              px: 0.5,
              paddingBottom: 0.5,
              width: "90%",
              whiteSpace: "nowrap",
              textOverflow: "ellipsis",
              overflow: "hidden",
            }}
          >
            {study.folder}
          </Typography>
        </Tooltip>
        <Box
          sx={{
            width: "100%",
            height: "25px",
            display: "flex",
            flexDirection: "row",
            justifyContent: "space-between",
            mt: 0,
          }}
        >
          <Box
            sx={{
              display: "flex",
              maxWidth: "65%",
              alignItems: "center",
            }}
          >
            <ScheduleOutlinedIcon sx={{ color: "text.secondary", mr: 1 }} />
            <TinyText noWrap>{convertUTCToLocalTime(study.creationDate)}</TinyText>
          </Box>
          <Box
            sx={{
              display: "flex",
              gap: 1,
            }}
          >
            <UpdateOutlinedIcon sx={{ color: "text.secondary" }} />
            <TinyText>{buildModificationDate(study.modificationDate, t, i18n.language)}</TinyText>
            <Divider flexItem orientation="vertical" />
            <TinyText>{`v${compactSemanticVersion(study.version)}`}</TinyText>
          </Box>
        </Box>
        <Box
          sx={{
            display: "flex",
            textOverflow: "ellipsis",
            overflow: "hidden",
            mt: 1,
            alignItems: "center",
            gap: 1,
          }}
        >
          <EditorIcon />
          <TinyText>{study.editor}</TinyText>
        </Box>
        <Box
          sx={{
            my: 1,
            width: 1,
            height: "38px",
            display: "flex",
            flexDirection: "row",
            flexWrap: "wrap",
            justifyContent: "flex-start",
            alignItems: "center",
            gap: 0.5,
          }}
        >
          {study.archived && (
            <Chip icon={<ArchiveOutlinedIcon />} label="archive" color="warning" />
          )}
          {study.type === StudyType.VARIANT && (
            <Chip
              icon={<AltRouteOutlinedIcon />}
              label={t("studies.variant").toLowerCase()}
              color={isDarkMode ? "primary" : "secondary"}
            />
          )}
          {study.managed ? (
            <Chip label={t("studies.managedStudy")} color="info" />
          ) : (
            <Chip label={study.workspace} />
          )}
          {study.tags?.map((tag) => (
            <Chip key={tag} label={tag} sx={{ bgcolor: colors.indigo[300] }} />
          ))}
        </Box>
      </CardContent>
      <CardActions>
        <RouterButton to="/studies/$studyId" params={{ studyId: study.id }}>
          {t("global.open")}
        </RouterButton>
        <Tooltip title={t("studies.moreActions")}>
          <Button
            color="primary"
            sx={{ width: "auto", minWidth: 0, p: 0 }}
            onClick={handleMenuOpen}
          >
            <MoreVertIcon />
          </Button>
        </Tooltip>
        <StudyActionsMenu
          open={!!anchorEl}
          anchorEl={anchorEl}
          onClose={handleMenuClose}
          study={study}
        />
      </CardActions>
    </Card>
  );
}, areEqual);

StudyCard.displayName = "StudyCard";

export default StudyCard;
