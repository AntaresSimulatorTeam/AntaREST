import React, { ReactNode } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  TextField,
  InputAdornment,
} from '@material-ui/core';
import SearchIcon from '@material-ui/icons/Search';
import { useTranslation } from 'react-i18next';
import AddIcon from '@material-ui/icons/Add';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      width: '100%',
      height: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      boxSizing: 'border-box',
    },
    search: {
      margin: theme.spacing(2),
    },
    button: {
      position: 'absolute',
      left: '20px',
      bottom: '25px',
      cursor: 'pointer',
      borderRadius: '50px',
      padding: theme.spacing(2),
      backgroundColor: theme.palette.secondary.main,
      color: 'white',
      '&:hover': {
        backgroundColor: theme.palette.secondary.dark,
      },
      height: '25px',
    },
  }));

interface PropsType {
    content: ReactNode | undefined;
    filter: ReactNode;
    onChange: (value: string) => void;
    onAdd: () => void;
}

const PropertiesView = (props: PropsType) => {
  const classes = useStyles();
  const { onAdd, onChange, content, filter } = props;
  const [t] = useTranslation();

  return (
    <div className={classes.root}>
      <TextField
        className={classes.search}
        label={t('main:search')}
        variant="outlined"
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon />
            </InputAdornment>
          ),
        }}
        onChange={(e) => onChange(e.target.value as string)}
      />
      {content}
      {filter}
      <AddIcon className={classes.button} onClick={onAdd} />
    </div>
  );
};

export default PropertiesView;
