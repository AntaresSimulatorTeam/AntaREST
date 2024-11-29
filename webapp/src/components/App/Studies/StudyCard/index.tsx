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

import { memo, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { AxiosError } from "axios";
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
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { indigo } from "@mui/material/colors";
import ScheduleOutlinedIcon from "@mui/icons-material/ScheduleOutlined";
import UpdateOutlinedIcon from "@mui/icons-material/UpdateOutlined";
import PersonOutlineIcon from "@mui/icons-material/PersonOutline";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ArchiveOutlinedIcon from "@mui/icons-material/ArchiveOutlined";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import AltRouteOutlinedIcon from "@mui/icons-material/AltRouteOutlined";
import debug from "debug";
import { areEqual } from "react-window";
import { StudyMetadata, StudyType } from "../../../../common/types";
import {
  buildModificationDate,
  convertUTCToLocalTime,
  displayVersionName,
} from "../../../../services/utils";
import useEnqueueErrorSnackbar from "../../../../hooks/useEnqueueErrorSnackbar";
import ExportModal from "../ExportModal";
import StarToggle from "../../../common/StarToggle";
import MoveStudyDialog from "../MoveStudyDialog";
import ConfirmationDialog from "../../../common/dialogs/ConfirmationDialog";
import useAppSelector from "../../../../redux/hooks/useAppSelector";
import { getStudy, isStudyFavorite } from "../../../../redux/selectors";
import useAppDispatch from "../../../../redux/hooks/useAppDispatch";
import { deleteStudy, toggleFavorite } from "../../../../redux/ducks/studies";
import PropertiesDialog from "../../Singlestudy/PropertiesDialog";
import ActionsMenu from "./ActionsMenu";
import type { DialogsType } from "./types";

const logError = debug("antares:studieslist:error");

interface Props {
  id: StudyMetadata["id"];
  setStudyToLaunch: (id: StudyMetadata["id"]) => void;
  width: number;
  height: number;
  selectionMode?: boolean;
  selected?: boolean;
  toggleSelect: (sid: string) => void;
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
    selectionMode = true,
    selected = false,
    toggleSelect,
  } = props;
  const [t, i18n] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [openDialog, setOpenDialog] = useState<DialogsType | null>(null);
  const study = useAppSelector((state) => getStudy(state, id));
  const isFavorite = useAppSelector((state) => isStudyFavorite(state, id));
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

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

  const handleFavoriteToggle = () => {
    dispatch(toggleFavorite(id));
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

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (!study) {
    return null;
  }

  return (
    <Card
      variant="outlined"
      sx={{
        width,
        height,
        display: "flex",
        flexDirection: "column",
        position: "relative",
      }}
      onClick={() => {
        if (selectionMode) {
          toggleSelect(study.id);
        }
      }}
    >
      {selectionMode && selected && (
        <Box
          sx={{
            position: "absolute",
            width: "100%",
            height: "100%",
            background: "rgba(0,0,0,0.3)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <CheckCircleIcon
            sx={{
              fontSize: "68px",
              opacity: 0.7,
            }}
            color="primary"
          />
        </Box>
      )}
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
            paddingTop: 0.5,
          }}
        >
          <Tooltip title={study.name}>
            <Typography
              noWrap
              variant="h6"
              component="div"
              onClick={() => navigate(`/studies/${study.id}`)}
              sx={{
                color: "white",
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
            <StarToggle
              isActive={isFavorite}
              activeTitle={t("studies.removeFavorite")}
              unactiveTitle={t("studies.addFavorite")}
              onToggle={handleFavoriteToggle}
            />
            <Tooltip title={t("study.copyId")}>
              <ContentCopyIcon
                sx={{
                  cursor: "pointer",
                  width: "16px",
                  height: "16px",
                  mx: 1,
                  color: "text.secondary",
                  "&:hover": { color: "primary.main" },
                }}
                onClick={handleCopyId}
              />
            </Tooltip>
          </Box>
        </Box>
        <Tooltip title={study.folder || ""}>
          <Typography
            variant="caption"
            component="div"
            sx={{
              color: "white",
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
            <TinyText noWrap>
              {convertUTCToLocalTime(study.creationDate)}
            </TinyText>
          </Box>
          <Box
            sx={{
              display: "flex",
              gap: 1,
            }}
          >
            <UpdateOutlinedIcon sx={{ color: "text.secondary" }} />
            <TinyText>
              {buildModificationDate(study.modificationDate, t, i18n.language)}
            </TinyText>
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
            ".MuiChip-root": {
              color: "black",
            },
          }}
        >
          {study.archived && (
            <Chip
              icon={<ArchiveOutlinedIcon />}
              label="archive"
              color="warning"
              size="small"
            />
          )}
          {study.type === StudyType.VARIANT && (
            <Chip
              icon={<AltRouteOutlinedIcon />}
              label={t("studies.variant").toLowerCase()}
              color="primary"
              size="small"
            />
          )}
          <Chip
            label={study.workspace}
            size="small"
            sx={{
              bgcolor: study.managed ? "secondary.main" : "gray",
            }}
          />
          {study.tags?.map((tag) => (
            <Chip
              key={tag}
              label={tag}
              size="small"
              sx={{ bgcolor: indigo[300] }}
            />
          ))}
        </Box>
      </CardContent>
      <CardActions>
        <NavLink to={`/studies/${study.id}`} style={{ textDecoration: "none" }}>
          <Button size="small" color="primary">
            {t("button.explore")}
          </Button>
        </NavLink>
        <Tooltip title={t("studies.moreActions")}>
          <Button
            size="small"
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
      <PropertiesDialog
        open={openDialog === "properties"}
        onClose={closeDialog}
        study={study}
      />
      <ConfirmationDialog
        title={t("dialog.title.confirmation")}
        onCancel={closeDialog}
        onConfirm={handleDelete}
        alert="warning"
        open={openDialog === "delete"}
      >
        {t("studies.question.delete")}
      </ConfirmationDialog>
      <ExportModal
        open={openDialog === "export"}
        onClose={closeDialog}
        study={study}
      />
      <MoveStudyDialog
        open={openDialog === "move"}
        onClose={closeDialog}
        study={study}
      />
    </Card>
  );
}, areEqual);

StudyCard.displayName = "StudyCard";

export default StudyCard;
