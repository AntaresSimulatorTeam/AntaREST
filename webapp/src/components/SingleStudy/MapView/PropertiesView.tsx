import React from 'react';
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
import { LinkProperties, NodeProperties } from './types';
import PanelView from './PanelView';

const buttonStyle = (theme: Theme, color: string) => ({
  width: '120px',
  border: `2px solid ${color}`,
  color,
  margin: theme.spacing(0.5),
  '&:hover': {
    color: 'white',
    backgroundColor: color,
  },
});

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
    button: {
      position: 'absolute',
      left: '10px',
      bottom: '10px',
      ...buttonStyle(theme, theme.palette.primary.main),
      boxSizing: 'border-box',
    },
    button2: {
      position: 'absolute',
      left: '150px',
      bottom: '10px',
      ...buttonStyle(theme, theme.palette.primary.main),
      boxSizing: 'border-box',
    },
  }));

interface PropsType {
    node?: NodeProperties;
    link?: LinkProperties;
    onClose?: () => void;
    onDelete?: (id: string, target?: string) => void;
    onArea?: () => void;
    onLink?: () => void;
}

const PropertiesView = (props: PropsType) => {
  const classes = useStyles();
  const { node, link, onClose, onDelete, onArea, onLink } = props;
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
      <Button className={classes.button} onClick={onArea}>
        {t('singlestudy:newArea')}
      </Button>
      <Button className={classes.button2} onClick={onLink}>
        {t('singlestudy:newLink')}
      </Button>
    </div>
  );
};

PropertiesView.defaultProps = {
  node: undefined,
  link: undefined,
  onClose: undefined,
  onDelete: undefined,
  onArea: undefined,
  onLink: undefined,
};

export default PropertiesView;
