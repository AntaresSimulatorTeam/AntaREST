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
    backgroundColor: 'white'
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
    borderRadius: '20px',
    padding: '0 10px',
    color: theme.palette.primary.main
  },
  searchicon :{
    color: theme.palette.primary.main
  },
  button: {
    borderRadius: '20px',
  },
  main: {
    flex: '1',
    width: '100%',
    display: 'flex',
    padding: '20px 50%',
    flexFlow: 'column nowrap',
    alignItems: 'center',
    overflowY: 'auto',
  },
  item: {
    flex: 'none',
    width: '80%',
    display: 'flex',
    padding: '20px',
    flexFlow: 'column nowrap',
    backgroundColor: 'red',
    margin: '2px'
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
            onChange={(event) => debounce(searchFilter, 200)(event.target.value)} // Mettre le delay dans le fichier de config ?
            endAdornment = {(
              <InputAdornment position="start">
                <SearchIcon className={classes.searchicon} />
              </InputAdornment>
            )} 
          />
        <Button variant="contained"
                color="primary" 
                className={classes.button}
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

