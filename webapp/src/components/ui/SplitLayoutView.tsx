import React, { ReactNode } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  Paper,
  Typography,
} from '@material-ui/core';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      width: '99%',
      height: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      backgroundColor: 'white',
      margin: theme.spacing(1),
      boxSizing: 'border-box',
    },
    header: {
      width: '100%',
      height: '40px',
      boxSizing: 'border-box',
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      backgroundColor: theme.palette.primary.main,
      borderTopLeftRadius: theme.shape.borderRadius,
      borderTopRightRadius: theme.shape.borderRadius,
      paddingLeft: theme.spacing(2),
    },
    title: {
      fontWeight: 'bold',
      color: 'white',
    },
    layout: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      width: '100%',
      height: '100%',
    },
    right: {
      display: 'block',
      width: '80%',
      height: '100%',
      position: 'relative',
      backgroundColor: '#EEE',
    },
    left: {
      display: 'block',
      width: '20%',
      height: '100%',
      position: 'relative',
    },
  }));

interface Props {
  title: string;
  left: ReactNode;
  right: ReactNode;
}

const SplitLayoutView = (props: Props) => {
  const classes = useStyles();
  const { title, left, right } = props;

  return (
    <Paper className={classes.root}>
      <div className={classes.header}>
        <Typography className={classes.title}>{title}</Typography>
      </div>
      <div className={classes.layout}>
        <div className={classes.left}>
          {left}
        </div>
        <div className={classes.right}>
          {right}
        </div>
      </div>
    </Paper>
  );
};

export default SplitLayoutView;
