import React, { useState} from 'react';
import { createStyles, makeStyles, Theme } from '@material-ui/core';
import NavSettings from '../../components/Settings/NavSettings';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    height: '100%',
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'center'
  },
}));


interface PropTypes {
    items : {
        [item : string] : () => JSX.Element
    }
}

const GenericSettings = (props: PropTypes) => {

  const { items } = props;
  const classes = useStyles();

  const navList = Object.keys(items);
  console.log(navList);
  const [navState, setNavState] = useState<string>(navList[0]);
  const onItemClick = (item : string) => {
    setNavState(item);
  }

  return (
    <div className={classes.root}>
        <NavSettings  
          currentItem={navState}
          items={navList}
          onItemClick={onItemClick}
        />
        { items[navState]() }
    </div>
  );
};

export default GenericSettings;

