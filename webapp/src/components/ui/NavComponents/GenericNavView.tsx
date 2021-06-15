import React, { useState, useEffect } from 'react';
import { createStyles, makeStyles } from '@material-ui/core';
import Nav from './Nav';

const useStyles = makeStyles(() => createStyles({
  root: {
    height: '100%',
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'center',
  },
}));

interface PropTypes {
    items: {
        [item: string]: () => JSX.Element;
    };
    initialValue: string;
}

const GenericNavView = (props: PropTypes) => {
  const { items, initialValue } = props;
  const classes = useStyles();
  const [navList, setNavList] = useState<Array<string>>([]);
  const [navState, setNavState] = useState<string>(initialValue);
  const onItemClick = (item: string) => {
    setNavState(item);
  };

  useEffect(() => {
    const list = Object.keys(items);
    setNavList(list);

    if (list.find((item) => item === initialValue)) setNavState(initialValue);
    return () => {
      setNavList([]);
    };
  }, [items, initialValue]);

  return (
    <div className={classes.root}>
      <Nav
        currentItem={navState}
        items={navList}
        onItemClick={onItemClick}
      />
      { items[navState]() }
    </div>
  );
};

export default GenericNavView;
