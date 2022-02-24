import React, { useState } from 'react';
import { AxiosError } from 'axios';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { Box, Card, CardActions, CardContent, Button, Typography, Menu, MenuItem, ListItemIcon, ListItemText, Tooltip } from '@mui/material';
import { styled } from '@mui/material/styles';
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
import { GenericInfo, StudyMetadata } from '../../common/types';
import { exportStudy } from '../../services/api/study';
import enqueueErrorSnackbar from '../common/ErrorSnackBar';
import { modificationDate } from '../../services/utils';

interface Props {
  study: StudyMetadata
  favorite: boolean;
  onFavoriteClick: (value: GenericInfo) => void;
  onArchiveClick: (study: StudyMetadata) => void;
  onUnarchiveClick: (study: StudyMetadata) => void;
  onDeleteClick: (study: StudyMetadata) => void;
}

const TinyText = styled(Typography)(({ theme }) => ({
  fontSize: '16px',
  color: theme.palette.text.secondary,
}));

export default function StudyCard(props: Props) {
  const { study, favorite, onFavoriteClick, onUnarchiveClick, onArchiveClick, onDeleteClick } = props;
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

    if(days !== '')
      return `${days}`;
    
    if(hours !== '')
      return `${hours}`;

    if(minutes !== '')
    return `${minutes}`;

    return `${seconds}`;
  }

  const copyId = (): void => {
    try {
      navigator.clipboard.writeText(study.id);
      enqueueSnackbar(t('singlestudy:onStudyIdCopySuccess'), { variant: 'success' });
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('singlestudy:onStudyIdCopyError'), e as AxiosError);
    }
  };

  return (
    <Card variant="outlined" sx={{ minWidth: 275, flex: 'none' }}>
      <CardContent>
        <Box width="100%" height="60px" display="flex" flexDirection="row" justifyContent="space-between" p={0.5}>
          <Box display="flex" flexDirection="column" justifyContent="center"  alignItems="flex-start" width="calc(100% - 60px)" boxSizing="border-box">
            <Tooltip title={study.name}>
              <Typography width="100%" noWrap variant="h5" component="div" color="white" boxSizing="border-box">
                {study.name}
              </Typography>
            </Tooltip>
            <Typography noWrap color="white" sx={{ fontSize: '16px', color: 'text.secondary'}} >
                {study.id}
            </Typography>
          </Box>
          <Box display="flex"  height="30px" flexDirection="row" flex="0 0 60px" justifyContent="center"  alignItems="center">
            <Tooltip title={t('studymanager:copyID') as string}>
              <ContentCopyIcon sx={{ cursor: 'pointer', 
                                     width: '20px', 
                                     height: '20px', 
                                     '&:hover': { color: 'text.secondary'} }}
                                onClick={() => copyId()} />
            </Tooltip>
            {favorite ? <StarPurple500OutlinedIcon sx={{ cursor: 'pointer' }} onClick={handleFavoriteClick} color="primary" /> :
            <StarOutlineOutlinedIcon sx={{ cursor: 'pointer' }} onClick={handleFavoriteClick} color="primary" />
            }
          </Box>
        </Box>
        <Box width="100%" display="flex" flexDirection="row" justifyContent="space-between" mt={1}>
          <Box display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center">
            <ScheduleOutlinedIcon sx={{ color: 'text.secondary', mr: 1 }} />
            <TinyText>
              {study.creationDate}
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
      </CardContent>
      <CardActions>
        <Button size="small" color="primary">{t('studymanager:exploreButton')}</Button>
        <Button size="small"
                aria-controls="menu-elements"
                aria-haspopup="true"
                id="menu"
                color="primary" 
                sx={{ width: 'auto', minWidth: 0, p: 0 }} 
                onClick={handleClick}>
          <MoreVertIcon />
        </Button>
        <Menu
              id="menu-elements"
              anchorEl={anchorEl}
              keepMounted
              open={openMenu === 'menu'}
              onClose={handleClose}
            >
            { study.archived ? 
              <MenuItem onClick={() => { onUnarchiveClick(study); handleClose(); }}>
                <ListItemIcon>
                  <UnarchiveOutlinedIcon sx={{ color: 'action.active', width: '24px', height: '24px' }} />
                </ListItemIcon>
                <ListItemText>
                {t('studymanager:unarchive')}
                </ListItemText>
              </MenuItem> :
              <div>
              <MenuItem onClick={() => { exportStudy(study.id, false); handleClose(); }}>
                <ListItemIcon>
                  <DownloadOutlinedIcon sx={{ color: 'action.active', width: '24px', height: '24px' }} />
                </ListItemIcon>
                <ListItemText>
                  {t('studymanager:export')}
                </ListItemText>
              </MenuItem>
              {study.managed &&
              <MenuItem onClick={() => { onArchiveClick(study); handleClose(); }}>
                <ListItemIcon>
                  <ArchiveOutlinedIcon sx={{ color: 'action.active', width: '24px', height: '24px' }} />
                </ListItemIcon>
                <ListItemText>
                  {t('studymanager:archive')}
                </ListItemText>
              </MenuItem>}
              </div>
            }
            {
              study.managed && 
              <MenuItem onClick={() => { onDeleteClick(study); handleClose(); }}>
                <ListItemIcon>
                  <DeleteOutlinedIcon sx={{ color: 'error.light', width: '24px', height: '24px' }} />
                </ListItemIcon>
                <ListItemText sx={{ color: 'error.light' }}>
                  {t('studymanager:delete')}
                </ListItemText>
              </MenuItem>
            }
        </Menu>
      </CardActions>
    </Card>
  );
}

