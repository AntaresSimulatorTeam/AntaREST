import { useMemo, useState } from "react";
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
import { connect, ConnectedProps, useSelector } from "react-redux";
import { GenericInfo, StudyMetadata, VariantTree } from "../../common/types";
import { STUDIES_HEIGHT_HEADER } from "../../theme";
import {
  deleteStudy as callDeleteStudy,
  archiveStudy as callArchiveStudy,
  unarchiveStudy as callUnarchiveStudy,
} from "../../services/api/study";
import { AppState } from "../../redux/ducks";
import {
  removeStudies,
  toggleFavorite as dispatchToggleFavorite,
} from "../../redux/ducks/study";
import PropertiesDialog from "./PropertiesDialog";
import LauncherDialog from "../studies/LauncherDialog";
import {
  buildModificationDate,
  convertUTCToLocalTime,
  countAllChildrens,
} from "../../services/utils";
import useEnqueueErrorSnackbar from "../../hooks/useEnqueueErrorSnackbar";
import { isCurrentStudyFavorite } from "../../redux/selectors";
import ExportDialog from "../studies/ExportModal";
import StarToggle from "../common/StarToggle";
import ConfirmationDialog from "../common/dialogs/ConfirmationDialog";

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

const mapState = (state: AppState) => ({});

const mapDispatch = {
  removeStudy: (sid: string) => removeStudies([sid]),
  toggleFavorite: dispatchToggleFavorite,
};

const connector = connect(mapState, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;
interface OwnProps {
  study: StudyMetadata | undefined;
  parent: StudyMetadata | undefined;
  childrenTree: VariantTree | undefined;
  isExplorer?: boolean;
  openCommands?: () => void;
}
type PropTypes = PropsFromRedux & OwnProps;

function NavHeader(props: PropTypes) {
  const {
    study,
    parent,
    childrenTree,
    isExplorer,
    removeStudy,
    openCommands,
    toggleFavorite,
  } = props;
  const [t, i18n] = useTranslation();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [openMenu, setOpenMenu] = useState<string>("");
  const [openLauncherDialog, setOpenLauncherDialog] = useState<boolean>(false);
  const [openPropertiesDialog, setOpenPropertiesDialog] =
    useState<boolean>(false);
  const [openDeleteDialog, setOpenDeleteDialog] = useState<boolean>(false);
  const [openExportDialog, setOpenExportDialog] = useState<boolean>(false);
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const isStudyFavorite = useSelector(isCurrentStudyFavorite);

  const publicModeList: Array<GenericInfo> = [
    { id: "NONE", name: t("singlestudy:nonePublicModeText") },
    { id: "READ", name: t("singlestudy:readPublicModeText") },
    { id: "EXECUTE", name: t("singlestudy:executePublicModeText") },
    { id: "EDIT", name: t("singlestudy:editPublicModeText") },
    { id: "FULL", name: t("singlestudy:fullPublicModeText") },
  ];

  const getPublicModeLabel = useMemo(
    (): string => {
      const publicModeLabel = publicModeList.find(
        (elm) => elm.id === study?.publicMode
      );
      if (publicModeLabel) return publicModeLabel.name;
      return "";
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [study]
  );

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
    } else navigate("/studies");
  };

  const onLaunchClick = (): void => {
    setOpenLauncherDialog(true);
  };

  const archiveStudy = async (study: StudyMetadata) => {
    try {
      await callArchiveStudy(study.id);
    } catch (e) {
      enqueueErrorSnackbar(
        t("studymanager:archivefailure", { studyname: study.name }),
        e as AxiosError
      );
    }
  };

  const unarchiveStudy = async (study: StudyMetadata) => {
    try {
      await callUnarchiveStudy(study.id);
    } catch (e) {
      enqueueErrorSnackbar(
        t("studymanager:unarchivefailure", { studyname: study.name }),
        e as AxiosError
      );
    }
  };

  const deleteStudy = async (study: StudyMetadata) => {
    // eslint-disable-next-line no-alert
    try {
      await callDeleteStudy(study.id);
      removeStudy(study.id);
    } catch (e) {
      enqueueErrorSnackbar(
        t("studymanager:failtodeletestudy"),
        e as AxiosError
      );
      logError("Failed to delete study", study, e);
    }
  };

  const onDeleteStudy = () => {
    if (study) deleteStudy(study);
    setOpenDeleteDialog(false);
    navigate("/studies");
  };

  const copyId = async (): Promise<void> => {
    if (study) {
      try {
        await navigator.clipboard.writeText(study.id);
        enqueueSnackbar(t("singlestudy:onStudyIdCopySuccess"), {
          variant: "success",
        });
      } catch (e) {
        enqueueErrorSnackbar(
          t("singlestudy:onStudyIdCopyError"),
          e as AxiosError
        );
      }
    }
  };

  return (
    <Box
      p={2}
      width="100%"
      height={`${STUDIES_HEIGHT_HEADER}px`}
      display="flex"
      flexDirection="column"
      justifyContent="flex-start"
      alignItems="center"
      boxSizing="border-box"
      overflow="hidden"
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
          {isExplorer === true && study ? study.name : t("main:studies")}
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
          <Tooltip title={study?.folder || ""}>
            <Typography variant="h6" sx={{ color: "text.primary" }}>
              {study?.name}
            </Typography>
          </Tooltip>
          <StarToggle
            isActive={isStudyFavorite}
            activeTitle={t("studymanager:removeFavorite") as string}
            unactiveTitle={t("studymanager:bookmark") as string}
            onToggle={() => {
              if (study) {
                toggleFavorite({ id: study.id, name: study.name });
              }
            }}
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
              onClick={copyId}
            />
          </Tooltip>
          {study?.managed && (
            <Chip
              label={t("singlestudy:managedStudy")}
              variant="outlined"
              color="secondary"
              sx={{ mx: 2 }}
            />
          )}
        </Box>
        <Box
          display="flex"
          flexDirection="row"
          justifyContent="center"
          alignItems="center"
          boxSizing="border-box"
        >
          {isExplorer === true && (
            <Button
              size="small"
              variant="contained"
              color="primary"
              onClick={() => onLaunchClick()}
            >
              {t("main:launch")}
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
                <ListItemText>{t("studymanager:unarchive")}</ListItemText>
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
                  <ListItemText>{t("singlestudy:properties")}</ListItemText>
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
                  <ListItemText>{t("studymanager:export")}</ListItemText>
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
                    <ListItemText>{t("studymanager:archive")}</ListItemText>
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
                  {t("studymanager:delete")}
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
          {parent && (
            <Box
              mx={3}
              display="flex"
              flexDirection="row"
              justifyContent="flex-start"
              alignItems="center"
            >
              <AltRouteOutlinedIcon sx={{ color: "text.secondary", mr: 1 }} />
              <LinkText to={`/studies/${parent.id}`}>{parent.name}</LinkText>
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
            <TinyText>{getPublicModeLabel}</TinyText>
          </Box>
        </Box>
      )}
      {openLauncherDialog && (
        <LauncherDialog
          open={openLauncherDialog}
          study={study}
          onClose={() => setOpenLauncherDialog(false)}
        />
      )}
      {openPropertiesDialog && study && (
        <PropertiesDialog
          open={openPropertiesDialog}
          onClose={() => setOpenPropertiesDialog(false)}
          study={study as StudyMetadata}
        />
      )}
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

NavHeader.defaultProps = {
  isExplorer: undefined,
  openCommands: undefined,
};

export default connector(NavHeader);
