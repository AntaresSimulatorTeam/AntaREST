import React, { useEffect, useRef } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
} from '@material-ui/core';
import LinkIcon from '@material-ui/icons/Link';
import { NodeProperties } from './types';
import { rgbToHsl } from '../../../services/utils';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      width: '100%',
      height: '100%',
      display: 'flex',
      padding: theme.spacing(0.5),
      marginTop: '2px',
      marginLeft: '2px',
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
      fontSize: '16px',
    },
    linkIcon: {
      marginLeft: theme.spacing(1),
      color: theme.palette.secondary.main,
      '&:hover': {
        color: theme.palette.secondary.dark,
      },
    },
    highlighted: {
    },
  }));

interface PropType {
    node: NodeProperties;
    linkCreation: (id: string) => void;
}

const NodeView = (props: PropType) => {
  const classes = useStyles();
  const nodeRef = useRef<HTMLDivElement>(null);
  const { node, linkCreation } = props;

  const hslColors = rgbToHsl(node.color || 'rgb(211, 211, 211)');
  // const [r,g,b] = node.color.slice(4, -1).split(',').map(Number);

  // style={{ border: node.highlighted ? '#f00 solid 2px' : `hsl(${hslColors[0]}, ${hslColors[1]}%, ${hslColors[2]}%) solid 2px`, color: hslColors[2] >= 75 || (hslColors[0] >= 50 && hslColors[0] <= 60 && hslColors[2] >= 70) ? 'black' : 'white' }}

  useEffect(() => {
    if (nodeRef.current) {
      const parentNodeClickedWidth = nodeRef.current.parentElement?.parentElement?.parentElement?.getAttribute('width');
      const parentNodePrevWidth = nodeRef.current.parentElement?.parentElement?.parentElement?.getAttribute('prevWidth');
      if (node.highlighted) {
        if (parentNodeClickedWidth !== null && parentNodeClickedWidth && !parentNodePrevWidth) {
          const newSizeClickedWidth = parseInt(parentNodeClickedWidth, 10) + 32;
          // eslint-disable-next-line no-unused-expressions
          nodeRef.current.parentElement?.parentElement?.parentElement?.setAttribute('width', `${newSizeClickedWidth}`);
          // eslint-disable-next-line no-unused-expressions
          nodeRef.current.parentElement?.parentElement?.parentElement?.setAttribute('prevWidth', parentNodeClickedWidth);
          // eslint-disable-next-line no-unused-expressions
          nodeRef.current.parentElement?.style.setProperty('width', `${newSizeClickedWidth}px`);
        }
      } else if (parentNodePrevWidth) {
        const newSize = parseInt(parentNodePrevWidth, 10);
        // eslint-disable-next-line no-unused-expressions
        nodeRef.current.parentElement?.parentElement?.parentElement?.setAttribute('width', `${newSize}`);
        // eslint-disable-next-line no-unused-expressions
        nodeRef.current.parentElement?.style.setProperty('width', `${newSize}px`);
        // eslint-disable-next-line no-unused-expressions
        nodeRef.current.parentElement?.parentElement?.parentElement?.removeAttribute('prevWidth');
      }
    }
  }, [node]);

  return (
    <div ref={nodeRef} className={classes.root}>
      {node.highlighted ? (
        <>
          <div className={`${classes.node} ${classes.highlighted}`} style={{ backgroundColor: `hsl(${hslColors[0]}, ${hslColors[1]}%, ${hslColors[2]}%)`, color: hslColors[2] >= 75 || (hslColors[0] >= 50 && hslColors[0] <= 75 && hslColors[2] >= 50) ? 'black' : 'white', boxShadow: `0px 0px 4px 2px hsl(${hslColors[0]}, ${hslColors[1]}%, ${hslColors[2]}%)` }}>
            {node.id}
          </div>
          <LinkIcon className={classes.linkIcon} onClick={(e) => { e.preventDefault(); e.stopPropagation(); linkCreation(node.id); }} />
        </>
      ) : (
        <div className={classes.node} style={{ backgroundColor: `hsl(${hslColors[0]}, ${hslColors[1]}%, ${hslColors[2]}%)`, color: hslColors[2] >= 75 || (hslColors[0] >= 50 && hslColors[0] <= 75 && hslColors[2] >= 50) ? 'black' : 'white' }}>
          {node.id}
        </div>
      )
      }
    </div>
  );
};

export default NodeView;
