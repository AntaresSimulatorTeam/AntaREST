import React, { useState } from 'react';
import { AxiosError } from 'axios';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { Box, Card, CardActions, CardContent, Button, Typography, Menu, MenuItem, ListItemIcon, ListItemText, Tooltip, Chip } from '@mui/material';
import { styled } from '@mui/material/styles';
import { indigo } from '@mui/material/colors';
import StarPurple500OutlinedIcon from '@mui/icons-material/StarPurple500Outlined';
import StarOutlineOutlinedIcon from '@mui/icons-material/StarOutlineOutlined';
import ScheduleOutlinedIcon from '@mui/icons-material/ScheduleOutlined';
import UpdateOutlinedIcon from '@mui/icons-material/UpdateOutlined';
import PersonOutlineIcon from '@mui/icons-material/PersonOutline';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import UnarchiveOutlinedIcon from '@mui/icons-material/UnarchiveOutlined';
import DownloadOutlinedIcon from '@mui/icons-material/DownloadOutlined';
import ArchiveOutlinedIcon from '@mui/icons-material/ArchiveOutlined';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import BoltIcon from '@mui/icons-material/Bolt';
import FileCopyOutlinedIcon from '@mui/icons-material/FileCopyOutlined';
import { GenericInfo, StudyMetadata } from '../../common/types';
import { exportStudy } from '../../services/api/study';
import enqueueErrorSnackbar from '../common/ErrorSnackBar';
import { convertUTCToLocalTime, modificationDate } from '../../services/utils';
import { scrollbarStyle } from '../../theme';

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
  fontSize: '16px',
  color: theme.palette.text.secondary,
}));

export default function StudyCard(props: Props) {
  const { study, width, favorite, onFavoriteClick, onLaunchClick, onImportStudy, onUnarchiveClick, onArchiveClick, onDeleteClick } = props;
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [openMenu, setOpenMenu] = useState<string>('');

  const handleFavoriteClick = () => {
    onFavoriteClick({ id: study.id, name: study.name });
  };

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
    setOpenMenu(event.currentTarget.id);
  };

  const handleClose = () => {
    setAnchorEl(null);
    setOpenMenu('');
  };

  const buildModificationDate = () : string => {
    const duration = modificationDate(study.modificationDate);
    const days = duration.days() > 0 ? `${duration.days().toString()} ${t('main:daysSymbol')}` : '';
    const hours = duration.hours() > 0 ? `${duration.hours().toString()} ${t('main:hoursSymbol')}` : '';
    const minutes = duration.minutes() > 0 ? `${duration.minutes().toString()} ${t('main:minutesSymbol')}` : '';
    const seconds = duration.seconds() > 0 ? `${duration.seconds().toString()} ${t('main:secondsSymbol')}` : '';

    if (days !== '') { return `${days}`; }

    if (hours !== '') { return `${hours}`; }

    if (minutes !== '') { return `${minutes}`; }

    return `${seconds}`;
  };

  const copyId = (): void => {
    try {
      navigator.clipboard.writeText(study.id);
      enqueueSnackbar(t('singlestudy:onStudyIdCopySuccess'), { variant: 'success' });
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('singlestudy:onStudyIdCopyError'), e as AxiosError);
    }
  };

  return (
    <Card variant="outlined" sx={{ width: width - 10, height: 250, marginLeft: '10px', marginTop: '5px', marginBottom: '5px', flex: 'none' }}>
      <CardContent>
        <Box width="100%" height="60px" display="flex" flexDirection="column" justifyContent="flex-start" p={0.5}>
          <Box display="flex" flexDirection="row" justifyContent="space-between" alignItems="flex-start" width="100%" boxSizing="border-box">
            <Tooltip title={study.name}>
              <Typography noWrap variant="h5" component="div" color="white" boxSizing="border-box">
                {study.name}
              </Typography>
            </Tooltip>
            {favorite ? <StarPurple500OutlinedIcon sx={{ cursor: 'pointer' }} onClick={handleFavoriteClick} color="primary" /> :
            <StarOutlineOutlinedIcon sx={{ cursor: 'pointer' }} onClick={handleFavoriteClick} color="primary" />
            }
          </Box>
          <Box display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center" width="100%" boxSizing="border-box">
            <Typography noWrap color="white" sx={{ fontSize: '13px', color: 'text.secondary' }}>
              {study.id}
            </Typography>
            <Tooltip title={t('studymanager:copyID') as string}>
              <ContentCopyIcon
                sx={{ cursor: 'pointer',
                  width: '16px',
                  height: '16px',
                  mx: 1,
                  color: 'text.secondary',
                  '&:hover': { color: 'primary.main' } }}
                onClick={() => copyId()}
              />
            </Tooltip>
          </Box>
        </Box>
        <Box width="100%" display="flex" flexDirection="row" justifyContent="space-between" mt={1}>
          <Box display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center">
            <ScheduleOutlinedIcon sx={{ color: 'text.secondary', mr: 1 }} />
            <TinyText>
              {convertUTCToLocalTime(study.creationDate)}
            </TinyText>
          </Box>
          <Box display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center">
            <UpdateOutlinedIcon sx={{ color: 'text.secondary', mr: 1 }} />
            <TinyText>
              {buildModificationDate()}
            </TinyText>
          </Box>
        </Box>
        <Box width="100%" display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center">
          <PersonOutlineIcon sx={{ color: 'text.secondary', mr: 1 }} />
          <TinyText>
            {study.owner.name}
          </TinyText>
        </Box>
        <Box
          my={1}
          width="100%"
          height="45px"
          display="flex"
          flexDirection="row"
          flexWrap="wrap"
          justifyContent="flex-start"
          alignItems="center"
          sx={{ overflowX: 'hidden', overflowY: 'auto', ...scrollbarStyle }}
        >
          <Chip
            label={study.workspace}
            variant="filled"
            sx={{ m: 0.25, bgcolor: study.managed ? 'secondary.main' : 'gray' }}
          />
          { study.tags &&
              study.tags.map((elm) => (
                <Chip
                  key={elm}
                  label={elm}
                  variant="filled"
                  sx={{ m: 0.25, bgcolor: indigo[300] }}
                />
              ))
          }
        </Box>
      </CardContent>
      <CardActions>
        <Button size="small" color="primary">{t('studymanager:exploreButton')}</Button>
        <Button
          size="small"
          aria-controls="menu-elements"
          aria-haspopup="true"
          id="menu"
          color="primary"
          sx={{ width: 'auto', minWidth: 0, p: 0 }}
          onClick={handleClick}
        >
          <MoreVertIcon />
        </Button>
        <Menu
          id="menu-elements"
          anchorEl={anchorEl}
          keepMounted
          open={openMenu === 'menu'}
          onClose={handleClose}
        >
          { study.archived ? (
            <MenuItem onClick={() => { onUnarchiveClick(study); handleClose(); }}>
              <ListItemIcon>
                <UnarchiveOutlinedIcon sx={{ color: 'action.active', width: '24px', height: '24px' }} />
              </ListItemIcon>
              <ListItemText>
                {t('studymanager:unarchive')}
              </ListItemText>
            </MenuItem>
          ) : (
            <div>
              <MenuItem onClick={() => { onLaunchClick(); handleClose(); }}>
                <ListItemIcon>
                  <BoltIcon sx={{ color: 'action.active', width: '24px', height: '24px' }} />
                </ListItemIcon>
                <ListItemText>
                  {t('main:launch')}
                </ListItemText>
              </MenuItem>
              <MenuItem onClick={() => { onImportStudy(study, false); handleClose(); }}>
                <ListItemIcon>
                  <FileCopyOutlinedIcon sx={{ color: 'action.active', width: '24px', height: '24px' }} />
                </ListItemIcon>
                <ListItemText>
                  {t('studymanager:importcopy')}
                </ListItemText>
              </MenuItem>
              <MenuItem onClick={() => { exportStudy(study.id, false); handleClose(); }}>
                <ListItemIcon>
                  <DownloadOutlinedIcon sx={{ color: 'action.active', width: '24px', height: '24px' }} />
                </ListItemIcon>
                <ListItemText>
                  {t('studymanager:export')}
                </ListItemText>
              </MenuItem>
              {study.managed && (
                <MenuItem onClick={() => { onArchiveClick(study); handleClose(); }}>
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
              study.managed && (
              <MenuItem onClick={() => { onDeleteClick(study); handleClose(); }}>
                <ListItemIcon>
                  <DeleteOutlinedIcon sx={{ color: 'error.light', width: '24px', height: '24px' }} />
                </ListItemIcon>
                <ListItemText sx={{ color: 'error.light' }}>
                  {t('studymanager:delete')}
                </ListItemText>
              </MenuItem>
              )}
        </Menu>
      </CardActions>
    </Card>
  );
}
