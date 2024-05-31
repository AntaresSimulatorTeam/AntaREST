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
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Tooltip,
  Chip,
  Divider,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { indigo } from "@mui/material/colors";
import ScheduleOutlinedIcon from "@mui/icons-material/ScheduleOutlined";
import UpdateOutlinedIcon from "@mui/icons-material/UpdateOutlined";
import PersonOutlineIcon from "@mui/icons-material/PersonOutline";
import DriveFileMoveIcon from "@mui/icons-material/DriveFileMove";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import UnarchiveOutlinedIcon from "@mui/icons-material/UnarchiveOutlined";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import ArchiveOutlinedIcon from "@mui/icons-material/ArchiveOutlined";
import DeleteOutlinedIcon from "@mui/icons-material/DeleteOutlined";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import BoltIcon from "@mui/icons-material/Bolt";
import FileCopyOutlinedIcon from "@mui/icons-material/FileCopyOutlined";
import AltRouteOutlinedIcon from "@mui/icons-material/AltRouteOutlined";
import debug from "debug";
import { areEqual } from "react-window";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import { StudyMetadata, StudyType } from "../../../common/types";
import {
  buildModificationDate,
  convertUTCToLocalTime,
  displayVersionName,
} from "../../../services/utils";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import ExportModal from "./ExportModal";
import StarToggle from "../../common/StarToggle";
import MoveStudyDialog from "./MoveStudyDialog";
import ConfirmationDialog from "../../common/dialogs/ConfirmationDialog";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import { getStudy, isStudyFavorite } from "../../../redux/selectors";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import { deleteStudy, toggleFavorite } from "../../../redux/ducks/studies";
import * as studyApi from "../../../services/api/study";
import PropertiesDialog from "../Singlestudy/PropertiesDialog";

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
  const [openMenu, setOpenMenu] = useState("");
  const [openPropertiesDialog, setOpenPropertiesDialog] = useState(false);
  const [openConfirmDeleteDialog, setOpenConfirmDeleteDialog] = useState(false);
  const [openExportModal, setOpenExportModal] = useState(false);
  const [openMoveDialog, setOpenMoveDialog] = useState(false);
  const study = useAppSelector((state) => getStudy(state, id));
  const isFavorite = useAppSelector((state) => isStudyFavorite(state, id));
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

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
    dispatch(deleteStudy({ id }))
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
        err,
      );
      logError("Failed to unarchive study", study, err);
    });
  };

  const handleArchiveClick = () => {
    studyApi.archiveStudy(id).catch((err) => {
      enqueueErrorSnackbar(
        t("studies.error.archive", { studyname: study?.name }),
        err,
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
      .copyStudy(id, `${study?.name} (${t("studies.copySuffix")})`, false)
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
                  sx={{
                    color: "action.active",
                    width: "24px",
                    height: "24px",
                  }}
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
              <MenuItem
                onClick={() => {
                  setOpenPropertiesDialog(true);
                  handleMenuClose();
                }}
              >
                <ListItemIcon>
                  <EditOutlinedIcon
                    sx={{
                      color: "action.active",
                      width: "24px",
                      height: "24px",
                    }}
                  />
                </ListItemIcon>
                <ListItemText>{t("study.properties")}</ListItemText>
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
                <ListItemText>{t("global.copy")}</ListItemText>
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
      {openPropertiesDialog && study && (
        <PropertiesDialog
          open={openPropertiesDialog}
          onClose={() => setOpenPropertiesDialog(false)}
          study={study}
        />
      )}
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
}, areEqual);

StudyCard.displayName = "StudyCard";

export default StudyCard;
