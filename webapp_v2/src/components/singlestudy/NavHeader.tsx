/* eslint-disable react-hooks/exhaustive-deps */
import React, { useEffect, useMemo, useState } from 'react';
import debug from 'debug';
import { Link, useNavigate } from 'react-router-dom';
import { AxiosError } from 'axios';
import { Box, Button, Chip, Divider, ListItemIcon, ListItemText, Menu, MenuItem, styled, Typography } from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import HistoryOutlinedIcon from '@mui/icons-material/HistoryOutlined';
import UnarchiveOutlinedIcon from '@mui/icons-material/UnarchiveOutlined';
import DownloadOutlinedIcon from '@mui/icons-material/DownloadOutlined';
import ArchiveOutlinedIcon from '@mui/icons-material/ArchiveOutlined';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import ScheduleOutlinedIcon from '@mui/icons-material/ScheduleOutlined';
import UpdateOutlinedIcon from '@mui/icons-material/UpdateOutlined';
import AltRouteOutlinedIcon from '@mui/icons-material/AltRouteOutlined';
import LanOutlinedIcon from '@mui/icons-material/LanOutlined';
import SecurityOutlinedIcon from '@mui/icons-material/SecurityOutlined';
import AccountTreeOutlinedIcon from '@mui/icons-material/AccountTreeOutlined';
import PersonOutlineOutlinedIcon from '@mui/icons-material/PersonOutlineOutlined';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import { connect, ConnectedProps } from 'react-redux';
import { GenericInfo, StudyMetadata, VariantTree } from '../../common/types';
import { STUDIES_HEIGHT_HEADER } from '../../theme';
import enqueueErrorSnackbar from '../common/ErrorSnackBar';
import { deleteStudy as callDeleteStudy, archiveStudy as callArchiveStudy, unarchiveStudy as callUnarchiveStudy, exportStudy } from '../../services/api/study';
import { AppState } from '../../store/reducers';
import { removeStudies } from '../../store/study';
import LauncherModal from '../studies/LauncherModal';
import PropertiesModal from './PropertiesModal';
import { buildModificationDate, convertUTCToLocalTime, countAllCHildrens } from '../../services/utils';
import DeleteStudyModal from '../studies/DeleteStudyModal';

const logError = debug('antares:singlestudy:navheader:error');

const TinyText = styled(Typography)(({ theme }) => ({
  fontSize: '14px',
  color: theme.palette.text.secondary,
}));

const LinkText = styled(Link)(({ theme }) => ({
  fontSize: '14px',
  color: theme.palette.secondary.main,
}));

const StyledDivider = styled(Divider)(({ theme }) => ({
  margin: theme.spacing(0, 1),
  width: '1px',
  height: '20px',
  backgroundColor: theme.palette.divider,
}));

const mapState = (state: AppState) => ({
});

const mapDispatch = ({
  removeStudy: (sid: string) => removeStudies([sid]),
});

const connector = connect(mapState, mapDispatch);
  type PropsFromRedux = ConnectedProps<typeof connector>;
  interface OwnProps {
    study: StudyMetadata | undefined;
    parent: StudyMetadata | undefined;
    childrenTree: VariantTree | undefined;
    isExplorer?: boolean;
}
type PropTypes = PropsFromRedux & OwnProps;

function NavHeader(props: PropTypes) {
  const { study, parent, childrenTree, isExplorer, removeStudy } = props;
  const [t, i18n] = useTranslation();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [openMenu, setOpenMenu] = useState<string>('');
  const [openLaunncherModal, setOpenLauncherModal] = useState<boolean>(false);
  const [openPropertiesModal, setOpenPropertiesModal] = useState<boolean>(false);
  const [openDeleteModal, setOpenDeleteModal] = useState<boolean>(false);
  const { enqueueSnackbar } = useSnackbar();

  const publicModeList: Array<GenericInfo> = [
    { id: 'NONE', name: t('singlestudy:nonePublicModeText') },
    { id: 'READ', name: t('singlestudy:readPublicModeText') },
    { id: 'EXECUTE', name: t('singlestudy:executePublicModeText') },
    { id: 'EDIT', name: t('singlestudy:editPublicModeText') },
    { id: 'FULL', name: t('singlestudy:fullPublicModeText') }];

  const getPublicModeLabel = useMemo(() : string => {
    const publicModeLabel = publicModeList.find((elm) => elm.id === study?.publicMode);
    if (publicModeLabel) return publicModeLabel.name;
    return '';
  }, [study]);

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
    setOpenMenu(event.currentTarget.id);
  };

  const handleClose = () => {
    setAnchorEl(null);
    setOpenMenu('');
  };

  const onBackClick = () => {
    if (isExplorer) { navigate(`/studies/${study?.id}`); } else navigate('/studies');
  };

  const onLaunchClick = () : void => {
    setOpenLauncherModal(true);
  };

  const archiveStudy = async (study: StudyMetadata) => {
    try {
      await callArchiveStudy(study.id);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:archivefailure', { studyname: study.name }), e as AxiosError);
    }
  };

  const unarchiveStudy = async (study: StudyMetadata) => {
    try {
      await callUnarchiveStudy(study.id);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:unarchivefailure', { studyname: study.name }), e as AxiosError);
    }
  };

  const deleteStudy = async (study: StudyMetadata) => {
    // eslint-disable-next-line no-alert
    try {
      await callDeleteStudy(study.id);
      removeStudy(study.id);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:failtodeletestudy'), e as AxiosError);
      logError('Failed to delete study', study, e);
    }
  };

  const onDeleteStudy = () => {
    if (study) deleteStudy(study);
    setOpenDeleteModal(false);
    navigate('/studies');
  };

  return (
    <Box p={2} width="100%" height={`${STUDIES_HEIGHT_HEADER}px`} display="flex" flexDirection="column" justifyContent="flex-start" alignItems="center" boxSizing="border-box" overflow="hidden">
      <Box width="100%" display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center" boxSizing="border-box">
        <ArrowBackIcon color="secondary" />
        <Button variant="text" color="secondary" onClick={onBackClick}>
          {isExplorer === true && study ? study.name : t('main:studies')}
        </Button>
      </Box>
      <Box width="100%" display="flex" flexDirection="row" justifyContent="space-between" alignItems="center" boxSizing="border-box">
        <Box width="100%" display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center" boxSizing="border-box">
          <Typography variant="h6" sx={{ color: 'text.primary' }}>{study?.name}</Typography>
          {study?.managed && <Chip label={t('singlestudy:managedStudy')} variant="outlined" color="secondary" sx={{ mx: 2 }} />}
        </Box>
        <Box display="flex" flexDirection="row" justifyContent="center" alignItems="center" boxSizing="border-box">
          {isExplorer === true && (
          <Button
            size="small"
            variant="contained"
            color="primary"
            onClick={() => onLaunchClick()}
          >
            {t('main:launch')}
          </Button>
          )}
          {isExplorer === true && (
          <Button
            size="small"
            variant="outlined"
            color="primary"
            sx={{ width: 'auto', minWidth: 0, mx: 2 }}
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
            sx={{ width: 'auto', minWidth: 0, px: 0 }}
            onClick={handleClick}
          >
            <MoreVertIcon />
          </Button>
          <Menu
            id="menu-study"
            anchorEl={anchorEl}
            keepMounted
            open={openMenu === 'menu-study'}
            onClose={handleClose}
          >
            { study?.archived ? (
              <MenuItem onClick={() => { unarchiveStudy(study); handleClose(); }}>
                <ListItemIcon>
                  <UnarchiveOutlinedIcon sx={{ color: 'action.active', width: '24px', height: '24px' }} />
                </ListItemIcon>
                <ListItemText>
                  {t('studymanager:unarchive')}
                </ListItemText>
              </MenuItem>
            ) : (
              <div>
                <MenuItem onClick={() => { setOpenPropertiesModal(true); handleClose(); }}>
                  <ListItemIcon>
                    <EditOutlinedIcon sx={{ color: 'action.active', width: '24px', height: '24px' }} />
                  </ListItemIcon>
                  <ListItemText>
                    {t('singlestudy:properties')}
                  </ListItemText>
                </MenuItem>
                <MenuItem onClick={() => {
                  if (study) exportStudy(study.id, false);
                  handleClose();
                }}
                >
                  <ListItemIcon>
                    <DownloadOutlinedIcon sx={{ color: 'action.active', width: '24px', height: '24px' }} />
                  </ListItemIcon>
                  <ListItemText>
                    {t('studymanager:export')}
                  </ListItemText>
                </MenuItem>
                {study?.managed && (
                <MenuItem onClick={() => { archiveStudy(study); handleClose(); }}>
                  <ListItemIcon>
                    <ArchiveOutlinedIcon sx={{ color: 'action.active', width: '24px', height: '24px' }} />
                  </ListItemIcon>
                  <ListItemText>
                    {t('studymanager:archive')}
                  </ListItemText>
                </MenuItem>
                )}
              </div>
            )}
            {
              study?.managed && (
              <MenuItem onClick={() => { setOpenDeleteModal(true); handleClose(); }}>
                <ListItemIcon>
                  <DeleteOutlinedIcon sx={{ color: 'error.light', width: '24px', height: '24px' }} />
                </ListItemIcon>
                <ListItemText sx={{ color: 'error.light' }}>
                  {t('studymanager:delete')}
                </ListItemText>
              </MenuItem>
              )}
          </Menu>
        </Box>
      </Box>
      {study && (
      <Box my={2} width="100%" display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center" boxSizing="border-box">
        <Box display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center">
          <ScheduleOutlinedIcon sx={{ color: 'text.secondary', mr: 1 }} />
          <TinyText>
            {convertUTCToLocalTime(study.creationDate)}
          </TinyText>
        </Box>
        <Box mx={3} display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center">
          <UpdateOutlinedIcon sx={{ color: 'text.secondary', mr: 1 }} />
          <TinyText>
            {buildModificationDate(study.modificationDate, t, i18n.language)}
          </TinyText>
        </Box>
        <StyledDivider />
        {parent && (
        <Box mx={3} display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center">
          <AltRouteOutlinedIcon sx={{ color: 'text.secondary', mr: 1 }} />
          <LinkText to={`/studies/${parent.id}`}>{parent.name}</LinkText>
        </Box>
        )}
        {childrenTree && (
        <Box mx={3} display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center">
          <AccountTreeOutlinedIcon sx={{ color: 'text.secondary', mr: 1 }} />
          <TinyText>
            {countAllCHildrens(childrenTree)}
          </TinyText>
        </Box>
        )}
        <StyledDivider />
        <Box mx={3} display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center">
          <PersonOutlineOutlinedIcon sx={{ color: 'text.secondary', mr: 1 }} />
          <TinyText>
            {study?.owner.name}
          </TinyText>
        </Box>
        <Box mx={3} display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center">
          <SecurityOutlinedIcon sx={{ color: 'text.secondary', mr: 1 }} />
          <TinyText>
            {getPublicModeLabel}
          </TinyText>
        </Box>
      </Box>
      )}
      {openLaunncherModal && <LauncherModal open={openLaunncherModal} study={study} onClose={() => setOpenLauncherModal(false)} />}
      {openPropertiesModal && study && <PropertiesModal open={openPropertiesModal} onClose={() => setOpenPropertiesModal(false)} study={study as StudyMetadata} />}
      {openDeleteModal && <DeleteStudyModal open={openDeleteModal} onClose={() => setOpenDeleteModal(false)} onYesClick={onDeleteStudy} />}
    </Box>
  );
}

NavHeader.defaultProps = {
  isExplorer: undefined,
};

export default connector(NavHeader);
