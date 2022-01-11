import React from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
} from '@material-ui/core';
import { NodeClickConfig } from './types';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      width: '100%',
      height: '100%',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
    },
    node: {
      backgroundColor: 'rgb(139,139,139)',
      opacity: '.8',
      minWidth: '10px',
      color: 'white',
      padding: theme.spacing(0.5),
      borderRadius: '20px',
    },
  }));

interface PropType {
    node: NodeClickConfig;
}

const NodeView = (props: PropType) => {
  const classes = useStyles();
  const { node } = props;

  return (
    <div className={classes.root}>
      <div className={classes.node}>
        {node.id}
      </div>
    </div>
  );
};

export default NodeView;
