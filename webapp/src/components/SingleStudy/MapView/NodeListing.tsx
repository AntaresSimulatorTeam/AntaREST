/* eslint-disable jsx-a11y/no-static-element-interactions */
import React from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
} from '@material-ui/core';
import AutoSizer from 'react-virtualized-auto-sizer';
import { FixedSizeList, areEqual, ListChildComponentProps } from 'react-window';
import { LinkProperties, NodeProperties } from './types';

const ROW_ITEM_SIZE = 60;

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      height: '500px',
      width: '90%',
      padding: theme.spacing(2),
      color: theme.palette.primary.main,
      flexGrow: 1,
      flexShrink: 1,
      marginBottom: '76px',
    },
  }));

interface PropsType {
    nodes: Array<NodeProperties>;
    setSelectedItem: (item: NodeProperties | LinkProperties) => void;
}

const Row = React.memo((props: ListChildComponentProps) => {
  const { data, index, style } = props;
  const { nodes, setSelectedItem } = data;
  const node = nodes[index];
  return (
    // eslint-disable-next-line jsx-a11y/click-events-have-key-events
    <div style={{ display: 'flex', justifyContent: 'center', ...style, top: `${parseFloat((style || {}).top as string) + 16}px`, cursor: 'pointer' }} onClick={() => setSelectedItem(node)}>
      {node.id}
    </div>
  );
}, areEqual);

const NodeListing = (props: PropsType) => {
  const classes = useStyles();
  const { nodes, setSelectedItem } = props;

  return (
    <div className={classes.root}>
      {nodes.length > 0 && nodes && (
        <AutoSizer>
          { ({ height, width }) => {
            const idealHeight = ROW_ITEM_SIZE * nodes.length;
            return (
              <FixedSizeList
                height={idealHeight > height ? height + ROW_ITEM_SIZE : idealHeight + ROW_ITEM_SIZE}
                width={width}
                itemCount={nodes.length}
                itemSize={ROW_ITEM_SIZE}
                itemData={{ nodes, setSelectedItem }}
              >
                {Row}
              </FixedSizeList>
            );
          }
          }
        </AutoSizer>
      )}
    </div>
  );
};

export default NodeListing;
