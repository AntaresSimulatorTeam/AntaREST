import React from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  ListItemText,
  ListItem,
  Typography,
  Button,
} from '@material-ui/core';
import DeleteIcon from '@material-ui/icons/Delete';
import { useTranslation } from 'react-i18next';
import AutoSizer from 'react-virtualized-auto-sizer';
import { areEqual, FixedSizeList, ListChildComponentProps } from 'react-window';
import { LinkProperties, NodeProperties } from './types';

const ROW_ITEM_SIZE = 40;
const BUTTONS_SIZE = 50;

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      width: '100%',
      padding: theme.spacing(1),
      flexGrow: 1,
      flexShrink: 1,
      minHeight: '100px',
      color: theme.palette.primary.main,
    },
    deleteIcon: {
      cursor: 'pointer',
      color: theme.palette.error.light,
      '&:hover': {
        color: theme.palette.error.main,
      },
    },
    buttons: {
      width: '100%',
      justifyContent: 'space-between',
      alignItems: 'center',
      display: 'flex',
      height: BUTTONS_SIZE,
    },
    title: {
      fontWeight: 'bold',
    },
  }));

interface PropsType {
    links: Array<LinkProperties>;
    node: NodeProperties;
    onDelete: (id: string, target?: string) => void;
}

const Row = React.memo((props: ListChildComponentProps) => {
  const { data, index, style } = props;
  const { links, node } = data;
  const link = links[index].source === node.id ? links[index].target : links[index].source;

  return (
    <ListItem key={index} style={style}>
      <ListItemText primary={link} />
    </ListItem>
  );
}, areEqual);

const LinksView = (props: PropsType) => {
  const classes = useStyles();
  const { links, node, onDelete } = props;
  const [t] = useTranslation();

  return (
    <div className={classes.root}>
      <Typography className={classes.title}>
        {t('singlestudy:link')}
      </Typography>
      <AutoSizer>
        {
          ({ height, width }) => {
            const idealHeight = ROW_ITEM_SIZE * links.length;
            return (
              <>
                <FixedSizeList height={idealHeight > height - BUTTONS_SIZE ? height - BUTTONS_SIZE : idealHeight} width={width} itemSize={ROW_ITEM_SIZE} itemCount={links.length} itemData={{ links, node }}>
                  {Row}
                </FixedSizeList>
                <div className={classes.buttons} style={{ width }}>
                  <Button color="primary" size="small">{t('singlestudy:more')}</Button>
                  <DeleteIcon className={classes.deleteIcon} onClick={() => { onDelete(node.id); }} />
                </div>
              </>
            );
          }
        }
      </AutoSizer>
    </div>
  );
};

export default LinksView;
