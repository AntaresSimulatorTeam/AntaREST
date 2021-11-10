/* eslint-disable react/no-array-index-key */
import React from 'react';
import { makeStyles, createStyles, Theme, Paper, Typography, Tooltip, Breadcrumbs, Grid } from '@material-ui/core';
import NavigateNextIcon from '@material-ui/icons/NavigateNext';
import FolderIcon from '@material-ui/icons/Folder';
import DescriptionIcon from '@material-ui/icons/Description';
import HomeRoundedIcon from '@material-ui/icons/HomeRounded';
import { StudyTreeNode } from '../utils';
import { StudyMetadata } from '../../../common/types';

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
      width: '120px',
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
      '&:hover': {
        color: theme.palette.secondary.main,
      },
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
    onDirClick: (element: string) => void;
}

const DirView = (props: Props) => {
  const classes = useStyles();
  const { node, onClick, dirPath, onDirClick } = props;

  const isDir = (element: StudyTreeNode | StudyMetadata) => (element as StudyMetadata).id === undefined;

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
                    onClick={() => onDirClick(elm)}
                  />
                ) : (
                  <Typography
                    key={`${elm}-${index}`}
                    className={classes.pathElement}
                    onClick={() => onDirClick(elm)}
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
            node.child.map((elm, index) =>
              (isDir(elm) ? (
                <Tooltip key={`${elm}-${index}`} title={elm.name}>
                  <Paper className={classes.element} onClick={() => onClick(elm)}>
                    <FolderIcon className={classes.icon} />
                    <div className={classes.elementNameContainer}>
                      <Typography noWrap className={classes.elementName}>{elm.name}</Typography>
                    </div>
                  </Paper>
                </Tooltip>
              ) : (
                <Tooltip key={`${elm}-${index}`} title={elm.name}>
                  <Paper className={classes.element} onClick={() => onClick(elm)}>
                    <DescriptionIcon className={classes.icon} />
                    <div className={classes.elementNameContainer}>
                      <Typography noWrap className={classes.elementName}>{elm.name}</Typography>
                    </div>
                  </Paper>
                </Tooltip>
              )))
        }
        </Grid>
      </div>
    </div>
  );
};

export default DirView;
