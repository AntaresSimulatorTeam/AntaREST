import React from 'react';
import { makeStyles, createStyles, Theme, useTheme } from '@material-ui/core';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemText from '@material-ui/core/ListItemText';
import { useTranslation } from 'react-i18next';

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
  itemSecondary: {
    backgroundColor: 'white',
    marginTop: theme.spacing(1),
    color: theme.palette.primary.main,
    '&:hover': {
      backgroundColor: theme.palette.primary.dark,
      color: 'white',
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
}));

interface PropTypes {
    onItemClick: (item: string) => void;
    currentItem: string;
    editionMode: boolean;
}

const Nav = (props: PropTypes) => {
  const classes = useStyles();
  const theme = useTheme();
  const { editionMode, currentItem, onItemClick } = props;
  const [t] = useTranslation();

  return (
    <div className={classes.root}>
      {
        !editionMode ? (
          <List className={classes.list}>
            <ListItem button onClick={() => onItemClick('singlestudy:variantDependencies')} className={currentItem === 'singlestudy:variantDependencies' ? classes.itemSelected : classes.item}>
              <ListItemText primary={t('singlestudy:variantDependencies')} />
            </ListItem>
            <ListItem button onClick={() => onItemClick('singlestudy:createVariant')} className={currentItem === 'singlestudy:createVariant' ? classes.itemSelected : classes.itemSecondary} style={{ marginBottom: theme.spacing(5) }}>
              <ListItemText primary={t('singlestudy:createVariant')} />
            </ListItem>
            <ListItem button onClick={() => onItemClick('singlestudy:editionMode')} className={currentItem === 'singlestudy:editionMode' ? classes.itemSelected : classes.item}>
              <ListItemText primary={t('singlestudy:editionMode')} />
            </ListItem>
          </List>
        ) : (
          <List className={classes.list}>
            <ListItem button onClick={() => onItemClick('singlestudy:variantDependencies')} className={currentItem === 'singlestudy:variantDependencies' ? classes.itemSelected : classes.item} style={{ marginBottom: theme.spacing(5) }}>
              <ListItemText primary={t('singlestudy:variantDependencies')} />
            </ListItem>
            <ListItem button onClick={() => onItemClick('singlestudy:editionMode')} className={currentItem === 'singlestudy:editionMode' ? classes.itemSelected : classes.item}>
              <ListItemText primary={t('singlestudy:editionMode')} />
            </ListItem>
            <ListItem button onClick={() => onItemClick('singlestudy:testGeneration')} className={currentItem === 'singlestudy:testGeneration' ? classes.itemSelected : classes.itemSecondary}>
              <ListItemText primary={t('singlestudy:testGeneration')} />
            </ListItem>
          </List>
        )}
    </div>
  );
};

export default Nav;
