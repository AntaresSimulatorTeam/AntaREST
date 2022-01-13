import React from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
} from '@material-ui/core';
import { NodeProperties } from './types';

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
      opacity: '.8',
      minWidth: '50px',
      color: 'white',
      textAlign: 'center',
      padding: theme.spacing(0.5),
      borderRadius: '30px',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap',
      height: '20px',
    },
  }));

interface PropType {
    node: NodeProperties;
}

const NodeView = (props: PropType) => {
  const classes = useStyles();
  const { node } = props;

  return (
    <div className={classes.root}>
      <div className={classes.node} style={{ backgroundColor: node.color }}>
        {node.id}
      </div>
    </div>
  );
};

export default NodeView;
