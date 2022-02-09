import React, { useState } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  TextField,
  InputAdornment,
  Button,
} from '@material-ui/core';
import SearchIcon from '@material-ui/icons/Search';
import { useTranslation } from 'react-i18next';
import AddIcon from '@material-ui/icons/Add';
import { LinkProperties, NodeProperties, UpdateAreaUi, isNode } from './types';
import PanelView from './PanelView';
import NodeListing from './NodeListing';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      width: '20%',
      height: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      boxSizing: 'border-box',
    },
    list: {
      minWidth: '75%',
      height: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'flex-start',
    },
    search: {
      margin: theme.spacing(2),
    },
    button: {
      position: 'absolute',
      left: '20px',
      bottom: '25px',
      cursor: 'pointer',
      borderRadius: '50px',
      padding: theme.spacing(2),
      backgroundColor: theme.palette.secondary.main,
      color: 'white',
      '&:hover': {
        backgroundColor: theme.palette.secondary.dark,
      },
      height: '25px',
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
    onArea?: () => void;
    onBlur: (id: string, value: UpdateAreaUi) => void;
}

const PropertiesView = (props: PropsType) => {
  const classes = useStyles();
  const { item, setSelectedItem, nodeList, nodeLinks, onDelete, onArea, onBlur } = props;
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
    <div className={classes.root}>
      <TextField
        className={classes.search}
        label={t('main:search')}
        variant="outlined"
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon />
            </InputAdornment>
          ),
        }}
        disabled
        onChange={(e) => onChange(e.target.value as string)}
      />
      {item && isNode(item) && onDelete ? (
        <div className={classes.list}>
          <Button className={classes.prevButton} size="small" onClick={() => setSelectedItem(undefined)}>{t('main:backButton')}</Button>
          <PanelView node={item as NodeProperties} links={nodeLinks} onDelete={onDelete} onBlur={onBlur} />
        </div>
      ) : (item && onDelete && (
        <div className={classes.list}>
          <Button className={classes.prevButton} size="small" onClick={() => setSelectedItem(undefined)}>{t('main:backButton')}</Button>
          <PanelView link={item as LinkProperties} onDelete={onDelete} onBlur={onBlur} />
        </div>
      ))}
      {filteredNodes && !item && (
        <NodeListing nodes={filteredNodes} setSelectedItem={setSelectedItem} />
      )}
      <AddIcon className={classes.button} onClick={onArea} />
    </div>
  );
};

PropertiesView.defaultProps = {
  item: undefined,
  nodeLinks: undefined,
  onDelete: undefined,
  onArea: undefined,
};

export default PropertiesView;
