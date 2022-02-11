import React, { useState } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  Button,
} from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import { LinkProperties, NodeProperties, UpdateAreaUi, isNode } from './types';
import PanelView from './PanelView';
import NodeListing from './NodeListing';
import PropertiesView from '../../ui/PropertiesView';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    list: {
      minWidth: '75%',
      height: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'flex-start',
    },
    prevButton: {
      color: theme.palette.primary.main,
    },
  }));

interface PropsType {
    item?: NodeProperties | LinkProperties | undefined;
    setSelectedItem: (item: NodeProperties | LinkProperties | undefined) => void;
    nodeList: Array<NodeProperties>;
    nodeLinks?: Array<LinkProperties> | undefined;
    onDelete?: (id: string, target?: string) => void;
    onArea: () => void;
    updateUI: (id: string, value: UpdateAreaUi) => void;
}

const MapPropsView = (props: PropsType) => {
  const classes = useStyles();
  const { item, setSelectedItem, nodeList, nodeLinks, onDelete, onArea, updateUI } = props;
  const [t] = useTranslation();
  const [filteredNodes, setFilteredNodes] = useState<Array<NodeProperties>>();

  const filter = (currentName: string): NodeProperties[] => {
    if (nodeList) {
      return nodeList.filter((s) => !currentName || (s.id.search(new RegExp(currentName, 'i')) !== -1));
    }
    return [];
  };

  const onChange = async (currentName: string) => {
    if (currentName !== '') {
      const f = filter(currentName);
      setFilteredNodes(f);
    } else {
      setFilteredNodes(undefined);
    }
  };

  return (
    <PropertiesView
      content={
        item && isNode(item) && onDelete ? (
          <div className={classes.list}>
            <Button className={classes.prevButton} size="small" onClick={() => setSelectedItem(undefined)}>{t('main:backButton')}</Button>
            <PanelView node={item as NodeProperties} links={nodeLinks} onDelete={onDelete} updateUI={updateUI} setSelectedItem={setSelectedItem} />
          </div>
        ) : (item && onDelete && (
          <div className={classes.list}>
            <Button className={classes.prevButton} size="small" onClick={() => setSelectedItem(undefined)}>{t('main:backButton')}</Button>
            <PanelView link={item as LinkProperties} nodes={nodeList} onDelete={onDelete} updateUI={updateUI} setSelectedItem={setSelectedItem} />
          </div>
        ))}
      filter={
        filteredNodes && !item && (
          <NodeListing nodes={filteredNodes} setSelectedItem={setSelectedItem} />
        )
      }
      onChange={(e) => onChange(e as string)}
      onAdd={onArea}
    />
  );
};

MapPropsView.defaultProps = {
  item: undefined,
  nodeLinks: undefined,
  onDelete: undefined,
};

export default MapPropsView;
