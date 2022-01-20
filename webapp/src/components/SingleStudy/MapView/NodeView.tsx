import React from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
} from '@material-ui/core';
import { ColorProperties, NodeProperties } from './types';
import { rgbToHsl } from '../../../services/utils';

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
      minWidth: '40px',
      textAlign: 'center',
      padding: theme.spacing(0.5),
      borderRadius: '30px',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap',
      height: '20px',
      backgroundColor: '#555',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
    },
    dot: {
      width: '0.5em',
      height: '0.5em',
      borderRadius: '50%',
      marginRight: theme.spacing(1),
    },
  }));

interface PropType {
    node: NodeProperties;
    color: ColorProperties;
}

const NodeView = (props: PropType) => {
  const classes = useStyles();
  const { node, color } = props;

  const hslColors = rgbToHsl(color.r, color.g, color.b);

  // style={{ border: node.highlighted ? '#f00 solid 2px' : `hsl(${hslColors[0]}, ${hslColors[1]}%, ${hslColors[2]}%) solid 2px`, color: hslColors[2] >= 75 || (hslColors[0] >= 50 && hslColors[0] <= 60 && hslColors[2] >= 70) ? 'black' : 'white' }}

  return (
    <div className={classes.root}>
      {node.highlighted ? (
        <div className={classes.node} style={{ backgroundColor: `hsl(${hslColors[0]}, ${hslColors[1]}%, ${hslColors[2]}%)`, color: hslColors[2] >= 75 || (hslColors[0] >= 50 && hslColors[0] <= 60 && hslColors[2] >= 70) ? 'black' : 'white' }}>
          {node.id}
        </div>
      ) : (
        <div className={classes.node} style={{ color: `hsl(${hslColors[0]}, ${hslColors[1]}%, ${hslColors[2]}%)` }}>
          {node.id}
        </div>
      )
      }
    </div>
  );
};

export default NodeView;
