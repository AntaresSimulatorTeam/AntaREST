import React from 'react';
import { makeStyles, createStyles } from '@material-ui/core';

const useStyles = makeStyles(() =>
  createStyles({
    root: {
      flex: 1,
      width: '100%',
      height: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'center',
      alignItems: 'center',
      overflowX: 'hidden',
      overflowY: 'auto',
      position: 'relative',
    },
  }));

interface Props {
  title: string;
  image: string;
}
const NoContentFound = (props: Props) => {
  const { title, image } = props;
  const classes = useStyles();

  return (
    <div className={classes.root}>
      <div>
        <img src={image} alt="no-content" />
      </div>
      <div>
        { title }
      </div>
    </div>
  );
};

export default NoContentFound;
