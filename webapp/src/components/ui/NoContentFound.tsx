import React, { ReactNode } from 'react';
import { makeStyles, Theme, createStyles } from '@material-ui/core';

const useStyles = makeStyles((theme: Theme) =>
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
      '&& div': {
        paddingTop: theme.spacing(1),
        paddingBottom: theme.spacing(1),
      },
    },
  }));

interface Props {
  title: string;
  icon: ReactNode;
  callToAction: ReactNode;
}
const NoContentFound = (props: Props) => {
  const { title, icon, callToAction } = props;
  const classes = useStyles();

  return (
    <div className={classes.root}>
      <div>
        { icon }
      </div>
      <div>
        { title }
      </div>
      <div>
        { callToAction }
      </div>
    </div>
  );
};

export default NoContentFound;
