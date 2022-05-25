import React, { useState } from "react";
import { NavLink } from "react-router-dom";
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
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Tooltip,
  Chip,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { indigo } from "@mui/material/colors";
import ScheduleOutlinedIcon from "@mui/icons-material/ScheduleOutlined";
import UpdateOutlinedIcon from "@mui/icons-material/UpdateOutlined";
import PersonOutlineIcon from "@mui/icons-material/PersonOutline";
import DriveFileMoveIcon from "@mui/icons-material/DriveFileMove";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import UnarchiveOutlinedIcon from "@mui/icons-material/UnarchiveOutlined";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import ArchiveOutlinedIcon from "@mui/icons-material/ArchiveOutlined";
import DeleteOutlinedIcon from "@mui/icons-material/DeleteOutlined";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import BoltIcon from "@mui/icons-material/Bolt";
import FileCopyOutlinedIcon from "@mui/icons-material/FileCopyOutlined";
import debug from "debug";
import { StudyMetadata } from "../../common/types";
import {
  buildModificationDate,
  convertUTCToLocalTime,
  displayVersionName,
} from "../../services/utils";
import { scrollbarStyle } from "../../theme";
import useEnqueueErrorSnackbar from "../../hooks/useEnqueueErrorSnackbar";
import ExportModal from "./ExportModal";
import StarToggle from "../common/StarToggle";
import MoveStudyDialog from "./MoveStudyDialog";
import ConfirmationDialog from "../common/dialogs/ConfirmationDialog";
import useAppSelector from "../../redux/hooks/useAppSelector";
import { getStudy, isStudyFavorite } from "../../redux/selectors";
import useAppDispatch from "../../redux/hooks/useAppDispatch";
import { deleteStudy, toggleFavorite } from "../../redux/ducks/studies";
import * as studyApi from "../../services/api/study";

const logError = debug("antares:studieslist:error");

interface Props {
  id: StudyMetadata["id"];
  setStudyToLaunch: (id: StudyMetadata["id"]) => void;
  width: number;
  height: number;
}

const TinyText = styled(Typography)(({ theme }) => ({
  fontSize: "16px",
  color: theme.palette.text.secondary,
}));

function StudyCard(props: Props) {
  const { id, width, height, setStudyToLaunch } = props;
  const [t, i18n] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [openMenu, setOpenMenu] = useState<string>("");
  const [openConfirmDeleteDialog, setOpenConfirmDeleteDialog] = useState(false);
  const [openExportModal, setOpenExportModal] = useState<boolean>(false);
  const [openMoveDialog, setOpenMoveDialog] = useState<boolean>(false);
  const study = useAppSelector((state) => getStudy(state, id));
  const isFavorite = useAppSelector((state) => isStudyFavorite(state, id));
  const dispatch = useAppDispatch();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleMenuOpen = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
    setOpenMenu(event.currentTarget.id);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setOpenMenu("");
  };

  const handleLaunchClick = () => {
    setStudyToLaunch(id);
    handleMenuClose();
  };

  const handleFavoriteToggle = () => {
    dispatch(toggleFavorite(id));
  };

  const handleDelete = () => {
    dispatch(deleteStudy(id))
      .unwrap()
      .catch((err) => {
        enqueueErrorSnackbar(t("studies.error.deleteStudy"), err as AxiosError);
        logError("Failed to delete study", study, err);
      });

    setOpenConfirmDeleteDialog(false);
  };

  const handleUnarchiveClick = () => {
    studyApi.unarchiveStudy(id).catch((err) => {
      enqueueErrorSnackbar(
        t("studies.error.unarchive", { studyname: study?.name }),
        err
      );
      logError("Failed to unarchive study", study, err);
    });
  };

  const handleArchiveClick = () => {
    studyApi.archiveStudy(id).catch((err) => {
      enqueueErrorSnackbar(
        t("studies.error.archive", { studyname: study?.name }),
        err
      );
      logError("Failed to archive study", study, err);
    });

    handleMenuClose();
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

  const handleCopyClick = () => {
    studyApi
      .copyStudy(id, `${study?.name} (${t("study.copyId")})`, false)
      .catch((err) => {
        enqueueErrorSnackbar(t("studies.error.copyStudy"), err);
        logError("Failed to copy study", study, err);
      });

    handleMenuClose();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (!study) {
    return null;
  }

  return (
    <Card variant="outlined" sx={{ width, height }}>
      <CardContent>
        <Box
          width="100%"
          height="40px"
          display="flex"
          flexDirection="row"
          justifyContent="flex-start"
          p={0.5}
        >
          <Tooltip title={study.name}>
            <Typography
              noWrap
              variant="h5"
              component="div"
              color="white"
              boxSizing="border-box"
              sx={{ width: "81%" }}
            >
              {study.name}
            </Typography>
          </Tooltip>
          <Box
            display="flex"
            justifyContent="center"
            alignItems="center"
            p={0}
            sx={{ flexFlow: "row nowrap" }}
          >
            <StarToggle
              isActive={isFavorite}
              activeTitle={t("studies.removeFavorite") as string}
              unactiveTitle={t("studies.bookmark") as string}
              onToggle={handleFavoriteToggle}
            />
            <Tooltip title={t("study.copyId") as string}>
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
        <Box
          width="100%"
          height="25px"
          display="flex"
          flexDirection="row"
          justifyContent="space-between"
          mt={0}
        >
          <Box
            display="flex"
            maxWidth="65%"
            flexDirection="row"
            justifyContent="flex-start"
            alignItems="center"
          >
            <ScheduleOutlinedIcon sx={{ color: "text.secondary", mr: 1 }} />
            <TinyText noWrap>
              {convertUTCToLocalTime(study.creationDate)}
            </TinyText>
          </Box>
          <Box
            display="flex"
            flexDirection="row"
            justifyContent="flex-start"
            alignItems="center"
          >
            <UpdateOutlinedIcon sx={{ color: "text.secondary", mr: 1 }} />
            <TinyText>
              {buildModificationDate(study.modificationDate, t, i18n.language)}
            </TinyText>
          </Box>
        </Box>
        <Box
          width="100%"
          display="flex"
          flexDirection="row"
          justifyContent="space-between"
          alignItems="center"
        >
          <Box
            display="flex"
            flexDirection="row"
            justifyContent="flex-start"
            alignItems="center"
          >
            <PersonOutlineIcon sx={{ color: "text.secondary", mr: 1 }} />
            <TinyText>{study.owner.name}</TinyText>
          </Box>
          <TinyText>{`v${displayVersionName(study.version)}`}</TinyText>
        </Box>
        <Box
          my={1}
          width="100%"
          height="70px"
          display="flex"
          flexDirection="row"
          flexWrap="wrap"
          justifyContent="flex-start"
          alignItems="center"
          sx={{ overflowX: "hidden", overflowY: "auto", ...scrollbarStyle }}
        >
          <Chip
            label={study.workspace}
            variant="filled"
            sx={{
              m: 0.25,
              color: "black",
              bgcolor: study.managed ? "secondary.main" : "gray",
            }}
          />
          {study.tags &&
            study.tags.map((elm) => (
              <Chip
                key={elm}
                label={elm}
                variant="filled"
                sx={{ m: 0.25, color: "black", bgcolor: indigo[300] }}
              />
            ))}
        </Box>
      </CardContent>
      <CardActions>
        {study.archived ? (
          <Button size="small" color="primary" onClick={handleUnarchiveClick}>
            {t("global.unarchive")}
          </Button>
        ) : (
          <NavLink
            to={`/studies/${study.id}`}
            style={{ textDecoration: "none" }}
          >
            <Button size="small" color="primary">
              {t("button.explore")}
            </Button>
          </NavLink>
        )}
        <Tooltip title={t("studies.moreActions") as string}>
          <Button
            size="small"
            aria-controls="menu-elements"
            aria-haspopup="true"
            id="menu"
            color="primary"
            sx={{ width: "auto", minWidth: 0, p: 0 }}
            onClick={handleMenuOpen}
          >
            <MoreVertIcon />
          </Button>
        </Tooltip>
        <Menu
          id="menu-elements"
          anchorEl={anchorEl}
          keepMounted
          open={openMenu === "menu"}
          onClose={handleMenuClose}
        >
          {study.archived ? (
            <MenuItem onClick={handleUnarchiveClick}>
              <ListItemIcon>
                <UnarchiveOutlinedIcon
                  sx={{ color: "action.active", width: "24px", height: "24px" }}
                />
              </ListItemIcon>
              <ListItemText>{t("global.unarchive")}</ListItemText>
            </MenuItem>
          ) : (
            <div>
              <MenuItem onClick={handleLaunchClick}>
                <ListItemIcon>
                  <BoltIcon
                    sx={{
                      color: "action.active",
                      width: "24px",
                      height: "24px",
                    }}
                  />
                </ListItemIcon>
                <ListItemText>{t("global.launch")}</ListItemText>
              </MenuItem>
              <MenuItem onClick={handleCopyClick}>
                <ListItemIcon>
                  <FileCopyOutlinedIcon
                    sx={{
                      color: "action.active",
                      width: "24px",
                      height: "24px",
                    }}
                  />
                </ListItemIcon>
                <ListItemText>{t("study.copyId")}</ListItemText>
              </MenuItem>
              {study.managed && (
                <MenuItem
                  onClick={() => {
                    setOpenMoveDialog(true);
                    handleMenuClose();
                  }}
                >
                  <ListItemIcon>
                    <DriveFileMoveIcon
                      sx={{
                        color: "action.active",
                        width: "24px",
                        height: "24px",
                      }}
                    />
                  </ListItemIcon>
                  <ListItemText>{t("studies.moveStudy")}</ListItemText>
                </MenuItem>
              )}
              <MenuItem
                onClick={() => {
                  setOpenExportModal(true);
                  handleMenuClose();
                }}
              >
                <ListItemIcon>
                  <DownloadOutlinedIcon
                    sx={{
                      color: "action.active",
                      width: "24px",
                      height: "24px",
                    }}
                  />
                </ListItemIcon>
                <ListItemText>{t("global.export")}</ListItemText>
              </MenuItem>
              {study.managed && (
                <MenuItem onClick={handleArchiveClick}>
                  <ListItemIcon>
                    <ArchiveOutlinedIcon
                      sx={{
                        color: "action.active",
                        width: "24px",
                        height: "24px",
                      }}
                    />
                  </ListItemIcon>
                  <ListItemText>{t("global.archive")}</ListItemText>
                </MenuItem>
              )}
            </div>
          )}
          {study.managed && (
            <MenuItem
              onClick={() => {
                setOpenConfirmDeleteDialog(true);
                handleMenuClose();
              }}
            >
              <ListItemIcon>
                <DeleteOutlinedIcon
                  sx={{ color: "error.light", width: "24px", height: "24px" }}
                />
              </ListItemIcon>
              <ListItemText sx={{ color: "error.light" }}>
                {t("global.delete")}
              </ListItemText>
            </MenuItem>
          )}
        </Menu>
      </CardActions>
      {openConfirmDeleteDialog && (
        <ConfirmationDialog
          title={t("dialog.title.confirmation")}
          onCancel={() => setOpenConfirmDeleteDialog(false)}
          onConfirm={handleDelete}
          alert="warning"
          open
        >
          {t("studies.question.delete")}
        </ConfirmationDialog>
      )}
      {openExportModal && (
        <ExportModal
          open={openExportModal}
          onClose={() => setOpenExportModal(false)}
          study={study}
        />
      )}
      {openMoveDialog && (
        <MoveStudyDialog
          open={openMoveDialog}
          onClose={() => setOpenMoveDialog(false)}
          study={study}
        />
      )}
    </Card>
  );
}

export default StudyCard;
