import React, { useState } from 'react';
import { createStyles, makeStyles } from '@material-ui/core/styles';
import SortButton from './SortButton';
import { SortStatus, SortItem } from './utils';

const useStyles = makeStyles(() =>
  createStyles({
    root: {
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
    },
  }));

  interface PropsType {
    itemNames: Array<string>;
    onClick: (item: SortItem) => void;
  }

const SortView = (props: PropsType) => {
  const classes = useStyles(props);
  const { itemNames, onClick } = props;
  const [items, setItems] = useState<Array<SortItem>>(itemNames.map((elm) => ({ name: elm, status: 'NONE' } as SortItem)));

  const onItemClick = (index: number, status: SortStatus) => {
    const tmpItems = items.map((elm, idx) => (idx === index ? elm : ({ name: elm.name, status: 'NONE' } as SortItem)));
    switch (status) {
      case 'INCREASE':
        tmpItems[index].status = 'DECREASE';
        break;
      case 'DECREASE':
        tmpItems[index].status = 'NONE';
        break;

      default:
        tmpItems[index].status = 'INCREASE';
        break;
    }

    setItems(tmpItems);
    onClick(tmpItems[index]);
  };

  return (
    <div className={classes.root}>
      {
            items.map((elm, index) =>
              <SortButton key={elm.name} label={elm.name} status={elm.status} onClick={() => onItemClick(index, elm.status)} />)
        }
    </div>
  );
};

export default SortView;
