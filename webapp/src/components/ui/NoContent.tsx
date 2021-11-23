import React, { ReactNode } from 'react';
import { makeStyles, Theme, createStyles } from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import LiveHelpRoundedIcon from '@material-ui/icons/LiveHelpRounded';

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
    liveHelpRoundedIcon: {
      color: theme.palette.primary.main,
      width: '100%',
      height: '100px',
    },
  }));

interface Props {
  title?: string;
  icon?: ReactNode;
  callToAction?: ReactNode;
}

const NoContent = (props: Props) => {
  const { title = 'main:noContent', icon, callToAction } = props;
  const [t] = useTranslation();
  const classes = useStyles();

  return (
    <div className={classes.root}>
      <div>
        { icon }
      </div>
      <div>
        { t(title) }
      </div>
      <div>
        { callToAction }
      </div>
    </div>
  );
};

NoContent.defaultProps = {
  title: 'main:noContent',
  icon: <LiveHelpRoundedIcon color="primary" style={{ height: '100px', width: '100%' }} />,
  callToAction: <div />,
};

export default NoContent;
