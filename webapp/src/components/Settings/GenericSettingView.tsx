import React, {PropsWithChildren} from 'react';
import { createStyles, makeStyles, Theme, InputBase, InputAdornment, Button } from '@material-ui/core';
import {debounce} from 'lodash';
import SearchIcon from '@material-ui/icons/Search';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    flex: '1',
    height: '100%',
    overflowY: 'auto',
    overflowX: 'hidden',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
  },
  header: {
    flex: '0 0 80px',
    width: '100%',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'space-evenly',
    alignItems: 'center',
  },
  searchbar: {
    flex: '0 0 60%',
    height: '50px',
    border: `2px solid ${theme.palette.primary.main}`,
    padding: theme.spacing(2),
    color: theme.palette.primary.main
  },
  searchicon :{
    color: theme.palette.primary.main
  },
  main: {
    flex: '1',
    width: '100%',
    display: 'flex',
    padding: theme.spacing(2),
    flexFlow: 'column nowrap',
    alignItems: 'center',
    overflowY: 'auto',
  }
}));


interface PropTypes {
    searchFilter: (input: string) => void,
    buttonValue: string,
    placeholder: string,
    onButtonClick: () => void
}


const GenericSettingView = (props: PropsWithChildren<PropTypes>) => {

  const { searchFilter, placeholder, buttonValue, onButtonClick, children } = props;
  const classes = useStyles();

  return (
    <div className={classes.root}>
      <div className={classes.header}>
        <InputBase
            className={classes.searchbar}
            placeholder={placeholder}
            onChange={(event) => debounce(searchFilter, 200)(event.target.value)}
            endAdornment = {(
              <InputAdornment position="start">
                <SearchIcon className={classes.searchicon} />
              </InputAdornment>
            )} 
          />
        <Button variant="contained"
                color="primary" 
                onClick={onButtonClick}>
          {buttonValue}
        </Button>     
      </div>
      <div className={classes.main}>
        {children}
      </div>
    </div>
  );
};

export default GenericSettingView;