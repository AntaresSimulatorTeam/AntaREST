import { useState } from "react";
import * as React from "react";
import debug from "debug";
import { useSnackbar } from "notistack";
import { Link, useNavigate } from "react-router-dom";
import { AxiosError } from "axios";
import {
  Box,
  Button,
  Chip,
  Divider,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  styled,
  Tooltip,
  Typography,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import ErrorIcon from "@mui/icons-material/Error";
import HistoryOutlinedIcon from "@mui/icons-material/HistoryOutlined";
import UnarchiveOutlinedIcon from "@mui/icons-material/UnarchiveOutlined";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import ArchiveOutlinedIcon from "@mui/icons-material/ArchiveOutlined";
import DeleteOutlinedIcon from "@mui/icons-material/DeleteOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import ScheduleOutlinedIcon from "@mui/icons-material/ScheduleOutlined";
import UpdateOutlinedIcon from "@mui/icons-material/UpdateOutlined";
import AltRouteOutlinedIcon from "@mui/icons-material/AltRouteOutlined";
import SecurityOutlinedIcon from "@mui/icons-material/SecurityOutlined";
import AccountTreeOutlinedIcon from "@mui/icons-material/AccountTreeOutlined";
import PersonOutlineOutlinedIcon from "@mui/icons-material/PersonOutlineOutlined";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { useTranslation } from "react-i18next";
import { indigo } from "@mui/material/colors";
import { StudyMetadata, VariantTree } from "../../../common/types";
import { STUDIES_HEIGHT_HEADER } from "../../../theme";
import {
  archiveStudy as callArchiveStudy,
  upgradeStudy as callUpgradeStudy,
  unarchiveStudy as callUnarchiveStudy,
} from "../../../services/api/study";
import { deleteStudy, toggleFavorite } from "../../../redux/ducks/studies";
import LauncherDialog from "../Studies/LauncherDialog";
import PropertiesDialog from "./PropertiesDialog";
import {
  buildModificationDate,
  convertUTCToLocalTime,
  countAllChildrens,
  displayVersionName,
} from "../../../services/utils";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import { isCurrentStudyFavorite } from "../../../redux/selectors";
import ExportDialog from "../Studies/ExportModal";
import StarToggle from "../../common/StarToggle";
import ConfirmationDialog from "../../common/dialogs/ConfirmationDialog";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import CheckBoxFE from "../../common/fieldEditors/CheckBoxFE";
import { PUBLIC_MODE_LIST } from "../../common/utils/constants";

const logError = debug("antares:singlestudy:navheader:error");

const TinyText = styled(Typography)(({ theme }) => ({
  fontSize: "14px",
  color: theme.palette.text.secondary,
}));

const LinkText = styled(Link)(({ theme }) => ({
  fontSize: "14px",
  color: theme.palette.secondary.main,
}));

const StyledDivider = styled(Divider)(({ theme }) => ({
  margin: theme.spacing(0, 1),
  width: "1px",
  height: "20px",
  backgroundColor: theme.palette.divider,
}));

const MAX_STUDY_TITLE_LENGTH = 45;

interface Props {
  study: StudyMetadata | undefined;
  parent: StudyMetadata | undefined;
  childrenTree: VariantTree | undefined;
  isExplorer?: boolean;
  openCommands?: VoidFunction;
  updateStudyData: VoidFunction;
}

function NavHeader(props: Props) {
  const {
    study,
    parent,
    childrenTree,
    isExplorer,
    openCommands,
    updateStudyData,
  } = props;
  const [t, i18n] = useTranslation();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [openMenu, setOpenMenu] = useState("");
  const [openLauncherDialog, setOpenLauncherDialog] = useState(false);
  const [openPropertiesDialog, setOpenPropertiesDialog] = useState(false);
  const [openUpgradeDialog, setOpenUpgradeDialog] = useState(false);
  const [deleteChildren, setDeleteChildren] = useState(false);
  const [openDeleteDialog, setOpenDeleteDialog] = useState(false);
  const [openExportDialog, setOpenExportDialog] = useState(false);
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const isStudyFavorite = useAppSelector(isCurrentStudyFavorite);
  const dispatch = useAppDispatch();

  const publicModeLabel =
    PUBLIC_MODE_LIST.find((mode) => mode.id === study?.publicMode)?.name || "";

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
    setOpenMenu(event.currentTarget.id);
  };

  const handleClose = () => {
    setAnchorEl(null);
    setOpenMenu("");
  };

  const onBackClick = () => {
    if (isExplorer) {
      navigate(`/studies/${study?.id}`);
    } else {
      navigate("/studies");
    }
  };

  const onLaunchClick = (): void => {
    setOpenLauncherDialog(true);
  };

  const archiveStudy = async (study: StudyMetadata) => {
    try {
      await callArchiveStudy(study.id);
    } catch (e) {
      enqueueErrorSnackbar(
        t("studies.error.archive", { studyname: study.name }),
        e as AxiosError
      );
    }
  };

  const unarchiveStudy = async (study: StudyMetadata) => {
    try {
      await callUnarchiveStudy(study.id);
    } catch (e) {
      enqueueErrorSnackbar(
        t("studies.error.unarchive", { studyname: study.name }),
        e as AxiosError
      );
    }
  };

  const upgradeStudy = async () => {
    if (study) {
      try {
        await callUpgradeStudy(study.id);
      } catch (e) {
        enqueueErrorSnackbar(
          t("study.error.upgrade", { studyname: study.name }),
          e as AxiosError
        );
      } finally {
        setOpenUpgradeDialog(false);
      }
    }
  };

  const onDeleteStudy = async () => {
    if (study) {
      try {
        await dispatch(deleteStudy({ id: study.id, deleteChildren })).unwrap();
        navigate(parent ? `/studies/${parent?.id}` : "/studies");
      } catch (err) {
        enqueueErrorSnackbar(t("studies.error.deleteStudy"), err as AxiosError);
        logError("Failed to delete study", study, err);
      } finally {
        setDeleteChildren(false);
        setOpenDeleteDialog(false);
      }
    }
  };

  const copyId = async (): Promise<void> => {
    if (study) {
      try {
        await navigator.clipboard.writeText(study.id);
        enqueueSnackbar(t("study.success.studyIdCopy"), {
          variant: "success",
        });
      } catch (e) {
        enqueueErrorSnackbar(t("study.error.studyIdCopy"), e as AxiosError);
      }
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        justifyContent: "flex-start",
        alignItems: "center",
        width: 1,
        height: STUDIES_HEIGHT_HEADER,
        p: 2,
        boxSizing: "border-box",
        overflow: "hidden",
      }}
    >
      <Box
        width="100%"
        display="flex"
        flexDirection="row"
        justifyContent="flex-start"
        alignItems="center"
        boxSizing="border-box"
      >
        <ArrowBackIcon
          color="secondary"
          onClick={onBackClick}
          sx={{ cursor: "pointer" }}
        />
        <Button variant="text" color="secondary" onClick={onBackClick}>
          <Tooltip
            title={isExplorer && study ? study.name : t("global.studies")}
            followCursor
          >
            <Typography variant="button">{t("global.studies")}</Typography>
          </Tooltip>
        </Button>
      </Box>
      <Box
        width="100%"
        display="flex"
        flexDirection="row"
        justifyContent="space-between"
        alignItems="center"
        boxSizing="border-box"
      >
        <Box
          width="100%"
          display="flex"
          flexDirection="row"
          justifyContent="flex-start"
          alignItems="center"
          boxSizing="border-box"
        >
          <Tooltip title={study?.folder || ""} placement="bottom-start">
            <Typography
              variant="h6"
              noWrap
              sx={{
                width: 1,
              }}
            >
              {study?.name}
            </Typography>
          </Tooltip>
          <StarToggle
            isActive={isStudyFavorite}
            activeTitle={t("studies.removeFavorite") as string}
            unactiveTitle={t("studies.bookmark") as string}
            onToggle={() => {
              if (study) {
                dispatch(toggleFavorite(study.id));
              }
            }}
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
              onClick={copyId}
            />
          </Tooltip>
          {study?.managed && (
            <Chip
              label={t("study.managedStudy")}
              variant="outlined"
              color="secondary"
              sx={{ ml: 2, mr: 1 }}
            />
          )}
          {!study?.managed && study?.workspace && (
            <Chip
              label={study.workspace}
              variant="outlined"
              sx={{ ml: 2, mr: 1 }}
            />
          )}
          {study?.tags &&
            study.tags.map((elm) => (
              <Chip
                key={elm}
                label={elm}
                variant="filled"
                sx={{ m: 0.25, color: "black", bgcolor: indigo[300] }}
              />
            ))}
          {isExplorer && (
            <Button
              size="small"
              variant="contained"
              color="primary"
              onClick={
                study?.archived ? () => unarchiveStudy(study) : onLaunchClick
              }
            >
              {study?.archived ? t("global.unarchive") : t("global.launch")}
            </Button>
          )}
          {study && study.type === "variantstudy" && (
            <Button
              size="small"
              variant="outlined"
              color="primary"
              onClick={openCommands}
              sx={{ width: "auto", minWidth: 0, marginLeft: 2 }}
            >
              <HistoryOutlinedIcon />
            </Button>
          )}
        </Box>
        <Box
          display="flex"
          flexDirection="row"
          justifyContent="center"
          alignItems="center"
          boxSizing="border-box"
        >
          <Button
            size="small"
            aria-controls="menu-study"
            aria-haspopup="true"
            id="menu-study"
            variant="outlined"
            color="primary"
            sx={{ width: "auto", minWidth: 0, px: 0, marginLeft: 2 }}
            onClick={handleClick}
          >
            <MoreVertIcon />
          </Button>
          <Menu
            id="menu-study"
            anchorEl={anchorEl}
            keepMounted
            open={openMenu === "menu-study"}
            onClose={handleClose}
          >
            {study?.archived ? (
              <MenuItem
                onClick={() => {
                  unarchiveStudy(study);
                  handleClose();
                }}
              >
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
                <MenuItem
                  onClick={() => {
                    setOpenPropertiesDialog(true);
                    handleClose();
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
                <MenuItem
                  onClick={() => {
                    setOpenUpgradeDialog(true);
                    handleClose();
                  }}
                >
                  <ListItemIcon>
                    <ErrorIcon
                      sx={{
                        color: "primary.main",
                        width: "24px",
                        height: "24px",
                      }}
                    />
                  </ListItemIcon>
                  <ListItemText>{t("study.upgrade")}</ListItemText>
                </MenuItem>
                <MenuItem
                  onClick={() => {
                    setOpenExportDialog(true);
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
                  <ListItemText>{t("global.export")}</ListItemText>
                </MenuItem>
                {study?.managed && (
                  <MenuItem
                    onClick={() => {
                      archiveStudy(study);
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
                    <ListItemText>{t("global.archive")}</ListItemText>
                  </MenuItem>
                )}
              </div>
            )}
            {study?.managed && (
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
                  {t("global.delete")}
                </ListItemText>
              </MenuItem>
            )}
          </Menu>
        </Box>
      </Box>
      {study && (
        <Box
          my={2}
          width="100%"
          display="flex"
          flexDirection="row"
          justifyContent="flex-start"
          alignItems="center"
          boxSizing="border-box"
        >
          <Box
            display="flex"
            flexDirection="row"
            justifyContent="flex-start"
            alignItems="center"
          >
            <ScheduleOutlinedIcon sx={{ color: "text.secondary", mr: 1 }} />
            <TinyText>{convertUTCToLocalTime(study.creationDate)}</TinyText>
          </Box>
          <Box
            mx={3}
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
          <StyledDivider />
          <Box
            mx={3}
            display="flex"
            flexDirection="row"
            justifyContent="flex-start"
            alignItems="center"
          >
            <TinyText>{`v${displayVersionName(study.version)}`}</TinyText>
          </Box>
          {parent && (
            <Box
              sx={{
                mx: 3,
                display: "flex",
                flexDirection: "row",
                justifyContent: "flex-start",
                alignItems: "center",
                whiteSpace: "nowrap",
                overflow: "hidden",
              }}
            >
              <AltRouteOutlinedIcon sx={{ color: "text.secondary", mr: 1 }} />
              <Tooltip title={parent.name}>
                <LinkText to={`/studies/${parent.id}`}>
                  {`${parent.name.substring(0, MAX_STUDY_TITLE_LENGTH)}...`}
                </LinkText>
              </Tooltip>
            </Box>
          )}
          {childrenTree && (
            <Box
              mx={3}
              display="flex"
              flexDirection="row"
              justifyContent="flex-start"
              alignItems="center"
            >
              <AccountTreeOutlinedIcon
                sx={{ color: "text.secondary", mr: 1 }}
              />
              <TinyText>{countAllChildrens(childrenTree)}</TinyText>
            </Box>
          )}
          <StyledDivider />
          <Box
            mx={3}
            display="flex"
            flexDirection="row"
            justifyContent="flex-start"
            alignItems="center"
          >
            <PersonOutlineOutlinedIcon
              sx={{ color: "text.secondary", mr: 1 }}
            />
            <TinyText>{study?.owner.name}</TinyText>
          </Box>
          <Box
            mx={3}
            display="flex"
            flexDirection="row"
            justifyContent="flex-start"
            alignItems="center"
          >
            <SecurityOutlinedIcon sx={{ color: "text.secondary", mr: 1 }} />
            <TinyText>{t(publicModeLabel)}</TinyText>
          </Box>
        </Box>
      )}
      {study && openLauncherDialog && (
        <LauncherDialog
          open={openLauncherDialog}
          studyIds={[study.id]}
          onClose={() => setOpenLauncherDialog(false)}
        />
      )}
      {openPropertiesDialog && study && (
        <PropertiesDialog
          open={openPropertiesDialog}
          onClose={() => setOpenPropertiesDialog(false)}
          study={study as StudyMetadata}
          updateStudyData={updateStudyData}
        />
      )}
      {openDeleteDialog && (
        <ConfirmationDialog
          title={t("dialog.title.confirmation")}
          onCancel={() => setOpenDeleteDialog(false)}
          onConfirm={onDeleteStudy}
          alert="warning"
          open
        >
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              alignItems: "flex-start",
              width: "100%",
              height: "auto",
              gap: 1,
            }}
          >
            <Typography>{t("studies.question.delete")}</Typography>
            <CheckBoxFE
              value={deleteChildren}
              label={t("studies.deleteSubvariants")}
              onChange={(e, checked) => setDeleteChildren(checked)}
            />
          </Box>
        </ConfirmationDialog>
      )}
      {openUpgradeDialog && (
        <ConfirmationDialog
          title={t("dialog.title.confirmation")}
          onCancel={() => setOpenUpgradeDialog(false)}
          onConfirm={upgradeStudy}
          alert="warning"
          open
        >
          <Typography>{t("study.question.upgrade")}</Typography>
        </ConfirmationDialog>
      )}
      {study && openExportDialog && (
        <ExportDialog
          open={openExportDialog}
          onClose={() => setOpenExportDialog(false)}
          study={study}
        />
      )}
    </Box>
  );
}

export default NavHeader;
