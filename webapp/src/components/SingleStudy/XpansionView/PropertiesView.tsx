import React, { useState } from 'react';
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
    list: {
      minWidth: '75%',
      height: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'flex-start',
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
    prevButton: {
      color: theme.palette.primary.main,
    },
  }));

interface PropsType {
    candidate?: string;
    candidateList: Array<string>;
    onAdd: () => void;
}

const PropertiesView = (props: PropsType) => {
  const classes = useStyles();
  const { candidate, candidateList, onAdd } = props;
  const [t] = useTranslation();
  const [filteredCandidates, setFilteredCandidates] = useState<Array<string>>();

  const filter = (currentName: string): string[] => {
    if (candidateList && candidate && filteredCandidates) {
      return candidateList.filter((s) => !currentName || (s.search(new RegExp(currentName, 'i')) !== -1));
    }
    return [];
  };

  const onChange = async (currentName: string) => {
    if (currentName !== '') {
      const f = filter(currentName);
      setFilteredCandidates(f);
    } else {
      setFilteredCandidates(undefined);
    }
  };

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
      <AddIcon className={classes.button} onClick={onAdd} />
    </div>
  );
};

PropertiesView.defaultProps = {
  candidate: undefined,
};

export default PropertiesView;
