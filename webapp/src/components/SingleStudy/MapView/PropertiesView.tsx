import React from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  TextField,
  InputAdornment,
} from '@material-ui/core';
import SearchIcon from '@material-ui/icons/Search';
import { useTranslation } from 'react-i18next';
import { LinkProperties, NodeProperties } from './types';
import PanelView from './PanelView';

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
    search: {
      marginTop: theme.spacing(2),
    },
  }));

interface PropsType {
    node?: NodeProperties;
    link?: LinkProperties;
    onClose?: () => void;
    onDelete?: (id: string, target?: string) => void;
}

const PropertiesView = (props: PropsType) => {
  const classes = useStyles();
  const { node, link, onClose, onDelete } = props;
  const [t] = useTranslation();

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
      />
      {node && onClose && onDelete ? (
        <PanelView node={node} onDelete={onDelete} />
      ) : (link && onClose && onDelete && (
        <PanelView link={link} onDelete={onDelete} />
      ))}
    </div>
  );
};

PropertiesView.defaultProps = {
  node: undefined,
  link: undefined,
  onClose: undefined,
  onDelete: undefined,
};

export default PropertiesView;
