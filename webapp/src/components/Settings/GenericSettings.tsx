import React, { useState, useEffect} from 'react';
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
    },
    initialValue: string;
}

const GenericSettings = (props: PropTypes) => {

  const { items, initialValue} = props;
  const classes = useStyles();
  const [navList, setNavList] = useState<Array<string>>([]);
  const [navState, setNavState] = useState<string>(initialValue);
  const onItemClick = (item : string) => {
    setNavState(item);
  }

  useEffect(() => {
    const list = Object.keys(items);
    setNavList(list);

    if(list.find((item) => item === initialValue))
        setNavState(initialValue);
    return () => {
      setNavList([]);
    }
  }, [items, initialValue])


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