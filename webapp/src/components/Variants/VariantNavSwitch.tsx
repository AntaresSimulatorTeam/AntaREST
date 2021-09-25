import React, { useState } from 'react';
import { makeStyles, createStyles, Theme, Switch, Typography, useTheme } from '@material-ui/core';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemText from '@material-ui/core/ListItemText';
import { useTranslation } from 'react-i18next';
import CreateVariantModal from './CreateVariantModal';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    flex: '0 0 20%',
    minWidth: '200px',
    height: '100%',
    overflowY: 'auto',
    overflowX: 'hidden',
  },
  userInfos: {
    padding: theme.spacing(1),
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    color: theme.palette.primary.main,
  },
  list: {
    padding: theme.spacing(2),
    alignItems: 'center',
  },
  item: {
    backgroundColor: theme.palette.primary.main,
    color: 'white',
    marginTop: theme.spacing(1),
    '&:hover': {
      backgroundColor: theme.palette.primary.dark,
    },
  },
  itemSelected: {
    backgroundColor: theme.palette.secondary.main,
    color: 'white',
    marginTop: theme.spacing(1),
    '&:hover': {
      backgroundColor: theme.palette.secondary.main,
    },
  },
  switchContainer: {
    width: '100%',
    height: '70px',
    padding: `${theme.spacing(1)} 0px`,
    display: 'flex',
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    // backgroundColor: 'red',
    marginBottom: '0px',
  },
  editModeTitle: {
    fontWeight: 'bold',
    color: theme.palette.primary.main,
    borderBottom: `4px solid ${theme.palette.primary.main}`,
  },
}));

interface PropTypes {
    onItemClick: (item: string) => void;
    studyId: string;
    currentItem: string;
    editionMode: boolean;
    onEditModeChange: () => void;
    editable: boolean;
}

const Nav = (props: PropTypes) => {
  const classes = useStyles();
  const { editable, editionMode, studyId, currentItem, onItemClick, onEditModeChange } = props;
  const [t] = useTranslation();
  const theme = useTheme();
  const [openModal, setOpenModal] = useState<boolean>(false);

  return (
    <div className={classes.root}>
      {
           editable && (
           <div className={classes.switchContainer}>
             <Switch
               checked={editionMode}
               onChange={onEditModeChange}
               name="Edition mode"
               color="primary"
               inputProps={{ 'aria-label': 'secondary checkbox' }}
             />
             <Typography className={classes.editModeTitle}>{t(editionMode ? 'variants:editionMode' : 'variants:variantMode')}</Typography>
           </div>
           )}
      {
        !editionMode ? (
          <List className={classes.list} style={{ paddingTop: editable ? '0px' : theme.spacing(2) }}>
            <ListItem button onClick={() => onItemClick('variants:variantDependencies')} className={currentItem === 'variants:variantDependencies' ? classes.itemSelected : classes.item}>
              <ListItemText primary={t('variants:variantDependencies')} />
            </ListItem>
            <ListItem button onClick={() => setOpenModal(true)} className={currentItem === 'variants:createVariant' ? classes.itemSelected : classes.item}>
              <ListItemText primary={t('variants:createVariant')} />
            </ListItem>
          </List>
        ) : (
          <List className={classes.list} style={{ paddingTop: editable ? '0px' : theme.spacing(2) }}>
            <ListItem button onClick={() => onItemClick('variants:editionMode')} className={currentItem === 'variants:editionMode' ? classes.itemSelected : classes.item}>
              <ListItemText primary={t('variants:editionMode')} />
            </ListItem>
            {
              /*
              <ListItem button onClick={() => onItemClick('variants:testGeneration')} className={currentItem === 'variants:testGeneration' ? classes.itemSelected : classes.item}>
                <ListItemText primary={t('variants:testGeneration')} />
              </ListItem>
              */
            }
          </List>
        )}
      <CreateVariantModal open={openModal} onClose={() => setOpenModal(false)} parentId={studyId} />
    </div>
  );
};

export default Nav;
