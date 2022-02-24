import React, { ReactNode } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  Paper,
  Typography,
  Divider,
  Box,
} from '@material-ui/core';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      width: '99%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      backgroundColor: 'white',
      margin: theme.spacing(1),
      boxSizing: 'border-box',
      flexGrow: 1,
      overflow: 'hidden',
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
      flexShrink: 0,
    },
    title: {
      fontWeight: 'bold',
      color: 'white',
    },
    layout: {
      display: 'flex',
      justifyContent: 'space-evenly',
      alignItems: 'center',
      width: '100%',
      overflow: 'hidden',
      flexGrow: 1,
    },
    right: {
      display: 'flex',
      alignItems: 'flex-start',
      justifyContent: 'center',
      width: '76%',
      height: '98%',
      position: 'relative',
    },
    left: {
      display: 'block',
      width: '20%',
      height: '100%',
      position: 'relative',
    },
    divider: {
      height: '96%',
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
      <Box className={classes.layout}>
        <Box className={classes.left}>
          {left}
        </Box>
        <Divider className={classes.divider} orientation="vertical" variant="middle" />
        <Box className={classes.right}>
          {right}
        </Box>
      </Box>
    </Paper>
  );
};

export default SplitLayoutView;
