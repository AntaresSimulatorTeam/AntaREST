/* eslint-disable react/no-array-index-key */
import React, { Fragment, useState } from 'react';
import clsx from 'clsx';
import { AxiosError } from 'axios';
import moment from 'moment';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import { makeStyles, createStyles, Theme, Paper, Typography, Tooltip, Breadcrumbs, Grid, Menu, MenuItem, useTheme } from '@material-ui/core';
import NavigateNextIcon from '@material-ui/icons/NavigateNext';
import FolderIcon from '@material-ui/icons/Folder';
import DescriptionIcon from '@material-ui/icons/Description';
import HomeRoundedIcon from '@material-ui/icons/HomeRounded';
import { isDir, StudyTreeNode } from '../utils';
import { StudyMetadata } from '../../../common/types';
import DownloadLink from '../../ui/DownloadLink';
import { getExportUrl } from '../../../services/api/study';
import ConfirmationModal from '../../ui/ConfirmationModal';
import enqueueErrorSnackbar from '../../ui/ErrorSnackBar';
import { convertUTCToLocalTime } from '../../../services/utils';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      width: '100%',
      height: '100%',
      overflow: 'hidden',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
    },
    header: {
      width: '100%',
      height: '40px',
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      padding: theme.spacing(0, 3),
      boxSizing: 'border-box',
      backgroundColor: theme.palette.grey[300],
    },
    dirView: {
      width: '100%',
      height: 'calc(100% - 40px)',
      overflowX: 'hidden',
      overflowY: 'auto',
      padding: theme.spacing(2, 2),
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      alignItems: 'flex-start',
      boxSizing: 'border-box',
      backgroundColor: theme.palette.grey[100],
    },
    pathElement: {
      color: theme.palette.primary.main,
      cursor: 'pointer',
      '&:hover': {
        textDecoration: 'underline',
      },
    },
    grid: {
      flex: 'none',
      width: 'auto',
      maxWidth: '100%',
      boxSizing: 'border-box',
    },
    element: {
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      boxSizing: 'border-box',
      width: '320px',
      backgrounCOlor: '#0000',
      padding: theme.spacing(2),
      margin: theme.spacing(3),
      cursor: 'pointer',
      '&:hover': {
        backgroundColor: theme.palette.grey[200],
      },
    },
    icon: {
      width: '50px',
      height: '50px',
      color: theme.palette.primary.main,
      boxSizing: 'border-box',
    },
    elementNameContainer: {
      display: 'flex',
      width: '100%',
      flex: 1,
      flexFlow: 'row nowrap',
      justifyContent: 'center',
      alignItems: 'center',
      boxSizing: 'border-box',
    },
    elementName: {
      color: theme.palette.primary.main,
      fontSize: '1em',
    },
    elementDate: {
      color: 'gray',
      fontSize: '0.8em',
    },
    secondaryColor: {
      color: theme.palette.secondary.main,
    },
    homeIcon: {
      color: theme.palette.primary.main,
      width: '16px',
      height: '16px',
      cursor: 'pointer',
      '&:hover': {
        color: theme.palette.secondary.main,
      },
    },
  }));

interface Props {
    dirPath: Array<string>;
    node: StudyTreeNode;
    onClick: (element: StudyTreeNode | StudyMetadata) => void;
    onDirClick: (element: Array<string>) => void;
    launchStudy: (study: StudyMetadata) => void;
    deleteStudy: (study: StudyMetadata) => void;
    importStudy: (study: StudyMetadata, withOutputs?: boolean) => void;
    archiveStudy: (study: StudyMetadata) => void;
    unarchiveStudy: (study: StudyMetadata) => void;
}

const DirView = (props: Props) => {
  const classes = useStyles();
  const theme = useTheme();
  const { node, onClick, dirPath, onDirClick, importStudy, launchStudy, deleteStudy, archiveStudy, unarchiveStudy } = props;
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);
  const [menuId, setMenuId] = useState<string>('');
  const [contextMenu, setContextMenu] = useState<{
    mouseX: number;
    mouseY: number;
  } | null>(null);

  const deleteStudyAndCloseModal = (study: StudyMetadata) => {
    deleteStudy(study);
    setOpenConfirmationModal(false);
  };

  const onContextMenu = (event: React.MouseEvent<HTMLDivElement, MouseEvent>, id: string) => {
    (event as any).preventDefault();
    setContextMenu(
      contextMenu === null
        ? {
          mouseX: event.clientX - 2,
          mouseY: event.clientY - 4,
        }
        : // repeated contextmenu when it is already open closes it with Chrome 84 on Ubuntu
      // Other native context menus might behave different.
      // With this behavior we prevent contextmenu from the backdrop to re-locale existing context menus.
        null,
    );
    setMenuId(id);
  };
  const handleClose = () => {
    setContextMenu(null);
  };

  const getMenuUnarchived = (study: StudyMetadata) => [

    (key: string) => <MenuItem key={key} onClick={() => launchStudy(study)} style={{ color: theme.palette.secondary.main }}>{t('main:launch')}</MenuItem>,
    (key: string) => <MenuItem key={key} onClick={() => importStudy(study)} style={{ color: theme.palette.primary.main }}>{t('studymanager:importcopy')}</MenuItem>,
    (key: string) => (
      <MenuItem key={key}>
        <DownloadLink url={getExportUrl(study.id, false)}>
          <span style={{ color: theme.palette.primary.main }}>{t('main:export')}</span>
        </DownloadLink>
      </MenuItem>
    ),

    (key: string) => study.managed &&
    <MenuItem key={key} onClick={() => archiveStudy(study)} style={{ color: theme.palette.primary.main }}>{t('studymanager:archive')}</MenuItem>,

  ];

  const copyId = (studyId: string): void => {
    try {
      navigator.clipboard.writeText(studyId);
      enqueueSnackbar(t('singlestudy:onStudyIdCopySuccess'), { variant: 'success' });
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('singlestudy:onStudyIdCopyError'), e as AxiosError);
    }
  };

  return (
    <div className={classes.root}>
      <div className={classes.header}>
        <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
          {
              dirPath.map((elm, index) => (
                index === 0 ? (
                  <HomeRoundedIcon
                    key={`${elm}-${index}`}
                    className={classes.homeIcon}
                    onClick={() => onDirClick(dirPath.slice(0, index + 1))}
                  />
                ) : (
                  <Typography
                    key={`${elm}-${index}`}
                    className={classes.pathElement}
                    onClick={() => onDirClick(dirPath.slice(0, index + 1))}
                  >
                    {elm}
                  </Typography>
                )
              ))
          }
        </Breadcrumbs>
      </div>
      <div className={classes.dirView}>
        <Grid container spacing={1} className={classes.grid} justify="center" alignItems="center">
          {
            node.children.map((elm, index) =>
              (isDir(elm) ? (
                <Tooltip key={`${elm.name}-${index}`} title={elm.name}>
                  <Paper className={classes.element} onClick={() => onClick(elm)}>
                    <FolderIcon className={classes.icon} />
                    <div className={classes.elementNameContainer}>
                      <Typography noWrap className={classes.elementName}>{elm.name}</Typography>
                    </div>
                    <div className={classes.elementNameContainer} style={{ justifyContent: 'center' }}>
                      <Typography noWrap className={classes.elementDate}>{convertUTCToLocalTime(elm.modificationDate)}</Typography>
                    </div>
                  </Paper>
                </Tooltip>
              ) : (
                <Fragment key={`${elm.name}-${index}`}>
                  <Tooltip title={elm.name}>
                    <Paper
                      className={classes.element}
                      onClick={() => onClick(elm)}
                      onContextMenu={(e) => onContextMenu(e, (elm as StudyMetadata).id)}
                      id={`paper-file-${elm.name}-${index}`}
                      aria-controls={`file-menu-${elm.name}-${index}`}
                      aria-haspopup="true"
                    >
                      <DescriptionIcon className={(elm as StudyMetadata).managed ? clsx(classes.icon, classes.secondaryColor) : classes.icon} />
                      <div className={classes.elementNameContainer}>
                        <Typography noWrap className={classes.elementName}>{elm.name}</Typography>
                      </div>
                      <div className={classes.elementNameContainer} style={{ justifyContent: 'center' }}>
                        <Typography noWrap className={classes.elementDate}>{convertUTCToLocalTime(elm.modificationDate)}</Typography>
                      </div>
                    </Paper>
                  </Tooltip>
                  <Menu
                    open={contextMenu !== null && menuId === (elm as StudyMetadata).id}
                    onClose={handleClose}
                    anchorReference="anchorPosition"
                    anchorPosition={
                      contextMenu !== null
                        ? { top: contextMenu.mouseY, left: contextMenu.mouseX }
                        : undefined
                    }
                  >
                    <MenuItem onClick={() => copyId((elm as StudyMetadata).id)} style={{ color: '#666' }}>{t('singlestudy:copyIdDir')}</MenuItem>
                    {
                        (elm as StudyMetadata).archived ?
                          <MenuItem onClick={() => unarchiveStudy(elm as StudyMetadata)}>{t('studymanager:unarchive')}</MenuItem> : (
                            getMenuUnarchived(elm as StudyMetadata).map((item, id) => item(`${(elm as StudyMetadata).id}-${index}-${id}`))
                          )}
                    {
                            (elm as StudyMetadata).managed &&
                            <MenuItem onClick={() => setOpenConfirmationModal(true)} style={{ color: theme.palette.error.main }}>{t('main:delete')}</MenuItem>
                    }
                  </Menu>
                  {openConfirmationModal && (
                    <ConfirmationModal
                      open={openConfirmationModal}
                      title={t('main:confirmationModalTitle')}
                      message={t('studymanager:confirmdelete')}
                      handleYes={() => deleteStudyAndCloseModal(elm as StudyMetadata)}
                      handleNo={() => setOpenConfirmationModal(false)}
                    />
                  )}
                </Fragment>
              )))
        }
        </Grid>
      </div>
    </div>
  );
};

export default DirView;
