import React from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  ListItemText,
  ListItem,
} from '@material-ui/core';
import { areEqual, FixedSizeList, ListChildComponentProps } from 'react-window';
import { LinkProperties, NodeProperties } from './types';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      width: '100%',
      maxHeight: '300px',
      maxWidth: '300px',
      padding: theme.spacing(1),
    },
  }));

interface PropsType {
    links: Array<LinkProperties>;
    node: NodeProperties;
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
  const { links, node } = props;

  return (
    <div className={classes.root}>
      <FixedSizeList height={300} width={300} itemSize={30} itemCount={links.length} itemData={{ links, node }}>
        {Row}
      </FixedSizeList>
    </div>
  );
};

export default LinksView;
