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

import { memo, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import type { AxiosError } from "axios";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import {
  Box,
  Card,
  CardActions,
  CardContent,
  Button,
  Typography,
  Tooltip,
  Chip,
  Divider,
  styled,
  colors,
  Checkbox,
} from "@mui/material";
import ScheduleOutlinedIcon from "@mui/icons-material/ScheduleOutlined";
import UpdateOutlinedIcon from "@mui/icons-material/UpdateOutlined";
import PersonOutlineIcon from "@mui/icons-material/PersonOutline";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import ArchiveOutlinedIcon from "@mui/icons-material/ArchiveOutlined";
import AltRouteOutlinedIcon from "@mui/icons-material/AltRouteOutlined";
import debug from "debug";
import { areEqual } from "react-window";
import { StudyType, type StudyMetadata } from "../../../../types/types";
import {
  buildModificationDate,
  convertUTCToLocalTime,
  displayVersionName,
} from "../../../../services/utils";
import useEnqueueErrorSnackbar from "../../../../hooks/useEnqueueErrorSnackbar";
import ExportModal from "../ExportModal";
import FavoriteStudyToggle from "../../../common/studies/FavoriteStudyToggle";
import MoveStudyDialog from "../MoveStudyDialog";
import ConfirmationDialog from "../../../common/dialogs/ConfirmationDialog";
import useAppSelector from "../../../../redux/hooks/useAppSelector";
import { getStudy } from "../../../../redux/selectors";
import useAppDispatch from "../../../../redux/hooks/useAppDispatch";
import { deleteStudy } from "../../../../redux/ducks/studies";
import PropertiesDialog from "../../Singlestudy/PropertiesDialog";
import ActionsMenu from "./ActionsMenu";
import type { DialogsType } from "./types";
import CopyButton from "@/components/common/buttons/CopyButton";
import useThemeColorScheme from "@/hooks/useThemeColorScheme";

const logError = debug("antares:studieslist:error");

interface Props {
  id: StudyMetadata["id"];
  setStudyToLaunch: (id: StudyMetadata["id"]) => void;
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
  const {
    id,
    width,
    height,
    setStudyToLaunch,
    isSelected,
    hasStudiesSelected,
    toggleStudySelection,
  } = props;
  const { t, i18n } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [openDialog, setOpenDialog] = useState<DialogsType | null>(null);
  const study = useAppSelector((state) => getStudy(state, id));
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { isDarkMode } = useThemeColorScheme();

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const closeDialog = () => {
    setOpenDialog(null);
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleMenuOpen = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleDelete = () => {
    dispatch(deleteStudy({ id }))
      .unwrap()
      .catch((err) => {
        enqueueErrorSnackbar(t("studies.error.deleteStudy"), err as AxiosError);
        logError("Failed to delete study", study, err);
      });

    setOpenDialog("delete");
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
        enqueueErrorSnackbar(t("study.error.studyIdCopy"), err);
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
              onClick={() => navigate(`/studies/${study.id}`)}
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
            <TinyText>{`v${displayVersionName(study.version)}`}</TinyText>
          </Box>
        </Box>
        <Box
          sx={{
            display: "flex",
            textOverflow: "ellipsis",
            overflow: "hidden",
            mt: 1,
          }}
        >
          <PersonOutlineIcon sx={{ color: "text.secondary" }} />
          <TinyText>{study.owner.name}</TinyText>
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
          <Chip label={study.workspace} color={study.managed ? "info" : "default"} />
          {study.tags?.map((tag) => (
            <Chip key={tag} label={tag} sx={{ bgcolor: colors.indigo[300] }} />
          ))}
        </Box>
      </CardContent>
      <CardActions>
        <NavLink to={`/studies/${study.id}`} style={{ textDecoration: "none" }}>
          <Button color="primary">{t("button.explore")}</Button>
        </NavLink>
        <Tooltip title={t("studies.moreActions")}>
          <Button
            id="menu"
            color="primary"
            sx={{ width: "auto", minWidth: 0, p: 0 }}
            onClick={handleMenuOpen}
          >
            <MoreVertIcon />
          </Button>
        </Tooltip>
        <ActionsMenu
          anchorEl={anchorEl}
          onClose={handleMenuClose}
          study={study}
          setStudyToLaunch={setStudyToLaunch}
          setOpenDialog={setOpenDialog}
        />
      </CardActions>
      {/* Keep conditional rendering for dialogs and not use only `open` property, because API calls are made on mount */}
      {openDialog === "properties" && <PropertiesDialog open onClose={closeDialog} study={study} />}
      {openDialog === "delete" && (
        <ConfirmationDialog
          open
          title={t("dialog.title.confirmation")}
          onCancel={closeDialog}
          onConfirm={handleDelete}
          alert="warning"
        >
          {t("studies.question.delete")}
        </ConfirmationDialog>
      )}
      {openDialog === "export" && <ExportModal open onClose={closeDialog} study={study} />}
      {openDialog === "move" && <MoveStudyDialog open onClose={closeDialog} study={study} />}
    </Card>
  );
}, areEqual);

StudyCard.displayName = "StudyCard";

export default StudyCard;
