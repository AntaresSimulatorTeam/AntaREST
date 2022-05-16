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
import { GenericInfo, StudyMetadata } from "../../common/types";
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

interface Props {
  study: StudyMetadata;
  width: number;
  favorite: boolean;
  onFavoriteClick: (value: GenericInfo) => void;
  onLaunchClick: () => void;
  onImportStudy: (study: StudyMetadata, withOutputs: boolean) => void;
  onArchiveClick: (study: StudyMetadata) => void;
  onUnarchiveClick: (study: StudyMetadata) => void;
  onDeleteClick: (study: StudyMetadata) => void;
}

const TinyText = styled(Typography)(({ theme }) => ({
  fontSize: "16px",
  color: theme.palette.text.secondary,
}));

export default function StudyCard(props: Props) {
  const {
    study,
    width,
    favorite,
    onFavoriteClick,
    onLaunchClick,
    onImportStudy,
    onUnarchiveClick,
    onArchiveClick,
    onDeleteClick,
  } = props;
  const [t, i18n] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [openMenu, setOpenMenu] = useState<string>("");
  const [openDeleteDialog, setOpenDeleteDialog] = useState<boolean>(false);
  const [openExportModal, setOpenExportModal] = useState<boolean>(false);
  const [openMoveDialog, setOpenMoveDialog] = useState<boolean>(false);

  const handleFavoriteClick = () => {
    onFavoriteClick({ id: study.id, name: study.name });
  };

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
    setOpenMenu(event.currentTarget.id);
  };

  const handleClose = () => {
    setAnchorEl(null);
    setOpenMenu("");
  };

  const copyId = (): void => {
    try {
      navigator.clipboard.writeText(study.id);
      enqueueSnackbar(t("singlestudy:onStudyIdCopySuccess"), {
        variant: "success",
      });
    } catch (e) {
      enqueueErrorSnackbar(
        t("singlestudy:onStudyIdCopyError"),
        e as AxiosError
      );
    }
  };

  const onDeleteStudy = () => {
    onDeleteClick(study);
    setOpenDeleteDialog(false);
  };

  return (
    <Card
      variant="outlined"
      sx={{
        width: width - 10,
        height: 250,
        marginLeft: "10px",
        marginTop: "5px",
        marginBottom: "5px",
        flex: "none",
      }}
    >
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
              isActive={favorite}
              activeTitle={t("studymanager:removeFavorite") as string}
              unactiveTitle={t("studymanager:bookmark") as string}
              onToggle={handleFavoriteClick}
            />
            <Tooltip title={t("studymanager:copyID") as string}>
              <ContentCopyIcon
                sx={{
                  cursor: "pointer",
                  width: "16px",
                  height: "16px",
                  mx: 1,
                  color: "text.secondary",
                  "&:hover": { color: "primary.main" },
                }}
                onClick={() => copyId()}
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
          <Button
            size="small"
            color="primary"
            onClick={() => onUnarchiveClick(study)}
          >
            {t("studymanager:unarchive")}
          </Button>
        ) : (
          <NavLink
            to={`/studies/${study.id}`}
            style={{ textDecoration: "none" }}
          >
            <Button size="small" color="primary">
              {t("studymanager:exploreButton")}
            </Button>
          </NavLink>
        )}
        <Tooltip title={t("singlestudy:more") as string}>
          <Button
            size="small"
            aria-controls="menu-elements"
            aria-haspopup="true"
            id="menu"
            color="primary"
            sx={{ width: "auto", minWidth: 0, p: 0 }}
            onClick={handleClick}
          >
            <MoreVertIcon />
          </Button>
        </Tooltip>
        <Menu
          id="menu-elements"
          anchorEl={anchorEl}
          keepMounted
          open={openMenu === "menu"}
          onClose={handleClose}
        >
          {study.archived ? (
            <MenuItem
              onClick={() => {
                onUnarchiveClick(study);
                handleClose();
              }}
            >
              <ListItemIcon>
                <UnarchiveOutlinedIcon
                  sx={{ color: "action.active", width: "24px", height: "24px" }}
                />
              </ListItemIcon>
              <ListItemText>{t("studymanager:unarchive")}</ListItemText>
            </MenuItem>
          ) : (
            <div>
              <MenuItem
                onClick={() => {
                  onLaunchClick();
                  handleClose();
                }}
              >
                <ListItemIcon>
                  <BoltIcon
                    sx={{
                      color: "action.active",
                      width: "24px",
                      height: "24px",
                    }}
                  />
                </ListItemIcon>
                <ListItemText>{t("main:launch")}</ListItemText>
              </MenuItem>
              <MenuItem
                onClick={() => {
                  onImportStudy(study, false);
                  handleClose();
                }}
              >
                <ListItemIcon>
                  <FileCopyOutlinedIcon
                    sx={{
                      color: "action.active",
                      width: "24px",
                      height: "24px",
                    }}
                  />
                </ListItemIcon>
                <ListItemText>{t("global:global.copy)}</ListItemText>
              </MenuItem>
              {study.managed && (
                <MenuItem
                  onClick={() => {
                    setOpenMoveDialog(true);
                    handleClose();
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
                  <ListItemText>{t("studymanager:moveStudy")}</ListItemText>
                </MenuItem>
              )}
              <MenuItem
                onClick={() => {
                  setOpenExportModal(true);
                  handleClose();
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
                <ListItemText>{t("global:global.export")}</ListItemText>
              </MenuItem>
              {study.managed && (
                <MenuItem
                  onClick={() => {
                    onArchiveClick(study);
                    handleClose();
                  }}
                >
                  <ListItemIcon>
                    <ArchiveOutlinedIcon
                      sx={{
                        color: "action.active",
                        width: "24px",
                        height: "24px",
                      }}
                    />
                  </ListItemIcon>
                  <ListItemText>{t("global:global.delete")}</ListItemText>
                </MenuItem>
              )}
            </div>
          )}
          {study.managed && (
            <MenuItem
              onClick={() => {
                setOpenDeleteDialog(true);
                handleClose();
              }}
            >
              <ListItemIcon>
                <DeleteOutlinedIcon
                  sx={{ color: "error.light", width: "24px", height: "24px" }}
                />
              </ListItemIcon>
              <ListItemText sx={{ color: "error.light" }}>
                {t("global:global.delete")}
              </ListItemText>
            </MenuItem>
          )}
        </Menu>
      </CardActions>
      {openDeleteDialog && (
        <ConfirmationDialog
          title={t("main:confirmationModalTitle")}
          onCancel={() => setOpenDeleteDialog(false)}
          onConfirm={onDeleteStudy}
          alert="warning"
          open
        >
          {t("studymanager:confirmdelete")}
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
