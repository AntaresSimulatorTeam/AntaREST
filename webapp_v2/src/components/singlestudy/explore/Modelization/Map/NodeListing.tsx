/* eslint-disable jsx-a11y/no-static-element-interactions */
import React from 'react';
import {
  Box,
  styled,
} from '@mui/material';
import AutoSizer from 'react-virtualized-auto-sizer';
import { FixedSizeList, areEqual, ListChildComponentProps } from 'react-window';
import { LinkProperties, NodeProperties } from '../../../../../common/types';
import { scrollbarStyle } from '../../../../../theme';

const ROW_ITEM_SIZE = 30;

const StyledList = styled(FixedSizeList)(({ theme }) => ({
  '&> div > div': {
    color: theme.palette.text.secondary,
    cursor: 'pointer',
    '&:hover': {
      color: theme.palette.text.primary,
      textDecoration: 'underline',
    },
  },
  ...scrollbarStyle,
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
    <Box style={{ display: 'flex', justifyContent: 'flex-start', ...style }} onClick={() => setSelectedItem(node)}>
      {node.name}
    </Box>
  );
}, areEqual);

function NodeListing(props: PropsType) {
  const { nodes, setSelectedItem } = props;

  return (
    <Box width="90%" height="500px" flexGrow={1} flexShrink={1} marginBottom="76px" sx={{ pl: 3, pt: 1, pr: 2 }}>
      {nodes.length > 0 && nodes && (
        <AutoSizer>
          { ({ height, width }) => {
            const idealHeight = ROW_ITEM_SIZE * nodes.length;
            return (
              <StyledList
                height={idealHeight > height ? height + ROW_ITEM_SIZE : idealHeight + ROW_ITEM_SIZE}
                width={width}
                itemCount={nodes.length}
                itemSize={ROW_ITEM_SIZE}
                itemData={{ nodes, setSelectedItem }}
              >
                {Row}
              </StyledList>
            );
          }
          }
        </AutoSizer>
      )}
    </Box>
  );
}

export default NodeListing;
