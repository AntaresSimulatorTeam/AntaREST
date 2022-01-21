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
import AddIcon from '@material-ui/icons/Add';
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
      padding: theme.spacing(1),
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
      /* taille fixe pour margin bottom de l'autre côté */
    },
    button2: {
      position: 'absolute',
      left: '150px',
      bottom: '10px',
      boxSizing: 'border-box',
      display: 'none',
    },
  }));

interface PropsType {
    item?: NodeProperties | LinkProperties | undefined;
    nodeLinks?: Array<LinkProperties> | undefined;
    onClose?: () => void;
    onDelete?: (id: string, target?: string) => void;
    onArea?: () => void;
    onLink?: () => void;
}

const PropertiesView = (props: PropsType) => {
  const classes = useStyles();
  const { item, nodeLinks, onClose, onDelete, onArea, onLink } = props;
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
      {item && Object.keys(item)[0] === 'id' && nodeLinks && onClose && onDelete ? (
        <PanelView node={item as NodeProperties} links={nodeLinks} onDelete={onDelete} />
      ) : (item && onClose && onDelete && (
        <PanelView link={item as LinkProperties} onDelete={onDelete} />
      ))}
      <AddIcon className={classes.button} onClick={onArea} />
      <Button className={classes.button2} onClick={onLink}>
        {t('singlestudy:newLink')}
      </Button>
    </div>
  );
};

PropertiesView.defaultProps = {
  item: undefined,
  nodeLinks: undefined,
  onClose: undefined,
  onDelete: undefined,
  onArea: undefined,
  onLink: undefined,
};

export default PropertiesView;
