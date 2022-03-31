import React from 'react';
import {
  ListItemText,
  ListItem,
  Typography,
  Box,
  styled,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import AutoSizer from 'react-virtualized-auto-sizer';
import { areEqual, FixedSizeList, ListChildComponentProps } from 'react-window';
import { LinkProperties, NodeProperties } from '../../../../../common/types';
import { StyledDeleteIcon } from './PanelView';

const ROW_ITEM_SIZE = 40;
const BUTTONS_SIZE = 50;

const hoverStyle = () => ({
  '&:hover': {
    textDecoration: 'underline',
  },
});

const StyledList = styled(FixedSizeList)(() => ({
  '&> div > li > div': {
    cursor: 'pointer',
    '&:hover': {
      textDecoration: 'underline',
    },
  },
}));

interface PropsType {
    links: Array<LinkProperties>;
    node: NodeProperties;
    onDelete: () => void;
    setSelectedItem: (item: NodeProperties | LinkProperties | undefined) => void;
}

const Row = React.memo((props: ListChildComponentProps) => {
  const { data, index, style } = props;
  const { links, node, setSelectedItem } = data;
  const link = links[index].source === node.id ? links[index].target : links[index].source;
  const linkData = links[index].source === node.id ? { source: links[index].source, target: links[index].target } : { source: links[index].target, target: links[index].source };

  return (
    <ListItem key={index} style={style}>
      <ListItemText primary={link} onClick={() => setSelectedItem(linkData)} style={{ width: '100%', ...hoverStyle }} />
    </ListItem>
  );
}, areEqual);

function LinksView(props: PropsType) {
  const { links, node, onDelete, setSelectedItem } = props;
  const [t] = useTranslation();

  return (
    <Box width="100%" flexGrow={1} flexShrink={1} minHeight="100px" padding="8px">
      {links.length >= 1 && (
      <Typography sx={{ width: '90%', marginBottom: '8px', boxSizing: 'border-box', fontWeight: 'bold' }}>
        {t('singlestudy:link')}
      </Typography>
      )}
      <AutoSizer>
        {
          ({ height, width }) => {
            const idealHeight = ROW_ITEM_SIZE * links.length;
            return (
              <>
                <StyledList height={idealHeight > height - BUTTONS_SIZE ? height - BUTTONS_SIZE : idealHeight} width={width} itemSize={ROW_ITEM_SIZE} itemCount={links.length} itemData={{ links, node, setSelectedItem }}>
                  {Row}
                </StyledList>
                <Box width="100%" height={BUTTONS_SIZE} display="flex" justifyContent="flex-end" alignItems="center" style={{ width }}>
                  <StyledDeleteIcon onClick={onDelete} />
                </Box>
              </>
            );
          }
        }
      </AutoSizer>
    </Box>
  );
}

export default LinksView;
