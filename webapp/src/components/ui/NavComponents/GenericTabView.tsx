import React, { useState, useEffect } from 'react';
import { makeStyles } from '@material-ui/core/styles';
import AppBar from '@material-ui/core/AppBar';
import Tabs from '@material-ui/core/Tabs';
import Tab from '@material-ui/core/Tab';
import { useTranslation } from 'react-i18next';
import { useHistory } from 'react-router';

const useStyles = makeStyles(() => ({
  root: {
    flex: 1,
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    overflow: 'hidden',
    boxSizing: 'border-box',
  },
  itemContainer: {
    height: '100%',
    width: '100%',
    position: 'relative',
    overflowY: 'hidden',
    boxSizing: 'border-box',
  },
}));

interface PropTypes {
    items: {
        [item: string]: () => JSX.Element;
    };
    studyId: string;
    initialValue: string;
}

export default function NavTabView(props: PropTypes) {
  const classes = useStyles();
  const { items, initialValue, studyId } = props;
  const history = useHistory();
  const [navList, setNavList] = useState<Array<string>>([]);
  const [navState, setNavState] = useState<string>(initialValue);
  const [t] = useTranslation();

  const handleChange = (event: React.ChangeEvent<{}>, newValue: number) => {
    setNavState(navList[newValue]);
    history.push(`/study/${studyId}/${navList[newValue]}`);
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
      <AppBar position="static">
        <Tabs
          variant="fullWidth"
          value={navList.findIndex((item) => item === navState)}
          onChange={handleChange}
          aria-label="nav tabs example"
        >
          {
            navList.map((item, index) => (
              <Tab
                key={item}
                onClick={(event: React.MouseEvent<HTMLAnchorElement, MouseEvent>) => {
                  event.preventDefault();
                }}
                label={t(`singlestudy:${item}`)}
                id={`nav-tab-${index}`}
                aria-controls={`nav-tabpanel-${index}`}
              />
            ))
        }
        </Tabs>
      </AppBar>
      {
        items[navState] && items[navState]()
      }
    </div>
  );
}
