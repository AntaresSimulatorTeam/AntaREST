import React, { useEffect, useState } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
} from '@material-ui/core';
import { ColorProperties, NodeProperties } from './types';

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
    color: ColorProperties;
}

const NodeView = (props: PropType) => {
  const classes = useStyles();
  const { node, color } = props;
  const [fontColor, setFontColor] = useState<string>('white');

  useEffect(() => {
    if ((color.r > 230 && color.g > 230) || (color.r > 220 && color.g > 220 && color.b > 220) || (color.r > 190 && color.g > 230 && color.b > 230)) {
      setFontColor('black');
    }
  }, [color]);

  return (
    <div className={classes.root}>
      <div className={classes.node} style={{ backgroundColor: node.highlighted ? '#f00' : `rgb(${color.r}, ${color.g}, ${color.b})`, color: fontColor }}>
        {node.id}
      </div>
    </div>
  );
};

export default NodeView;
