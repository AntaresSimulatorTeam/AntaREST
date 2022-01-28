import React, { useState } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  Typography,
  TextField,
  Button,
} from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import DeleteIcon from '@material-ui/icons/Delete';
import { NodeProperties, LinkProperties, UpdateAreaUi } from './types';
import ConfirmationModal from '../../ui/ConfirmationModal';
import LinksView from './LinksView';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    form: {
      display: 'flex',
      justifyContent: 'flex-start',
      alignItems: 'center',
      flexDirection: 'column',
      padding: theme.spacing(1),
      flexGrow: 1,
      marginBottom: '76px',
      width: '94%',
    },
    fields: {
      marginTop: theme.spacing(1),
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
    },
  }));

interface PropType {
    node?: NodeProperties;
    links?: Array<LinkProperties>;
    link?: LinkProperties;
    onDelete: (id: string, target?: string) => void;
    onBlur: (id: string, value: UpdateAreaUi) => void;
}

const PanelView = (props: PropType) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { node, links, link, onDelete, onBlur } = props;
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);

  return (
    <>
      <div className={classes.form}>
        {node && (
          <>
            <TextField className={classes.fields} label={t('singlestudy:areaName')} variant="filled" value={node.id} disabled />
            { /* eslint-disable-next-line @typescript-eslint/camelcase */ }
            <TextField className={classes.fields} label={t('singlestudy:color')} variant="filled" defaultValue={node.color} onBlur={(e) => onBlur(node.id, { x: node.x, y: node.y, color_rgb: e.target.value !== null ? (e.target.value).slice(4, -1).split(',').map(Number) : node.color.slice(4, -1).split(',').map(Number) })} />
            { /* eslint-disable-next-line @typescript-eslint/camelcase */ }
            <TextField className={classes.fields} label={t('singlestudy:posX')} variant="filled" value={node.x} disabled />
            { /* eslint-disable-next-line @typescript-eslint/camelcase */ }
            <TextField className={classes.fields} label={t('singlestudy:posY')} variant="filled" value={node.y} disabled />
          </>
        )}
        {links && node && (
          <LinksView links={links} node={node} onDelete={onDelete} />
        )}
        {link && (
        <>
          <Typography variant="body2" component="p">
            {link.source}
            <br />
            {link.target}
          </Typography>
          <div className={classes.buttons}>
            <Button color="primary" size="small">{t('singlestudy:more')}</Button>
            <DeleteIcon className={classes.deleteIcon} onClick={() => { onDelete(link.source, link.target); }} />
          </div>
        </>
        )}

      </div>
      {openConfirmationModal && node && (
        <ConfirmationModal
          open={openConfirmationModal}
          title={t('main:confirmationModalTitle')}
          message={t('singlestudy:confirmDeleteArea')}
          handleYes={() => { onDelete(node.id); setOpenConfirmationModal(false); }}
          handleNo={() => setOpenConfirmationModal(false)}
        />
      )}
      {openConfirmationModal && link && (
        <ConfirmationModal
          open={openConfirmationModal}
          title={t('main:confirmationModalTitle')}
          message={t('singlestudy:confirmDeleteLink')}
          handleYes={() => { onDelete(link.source, link.target); setOpenConfirmationModal(false); }}
          handleNo={() => setOpenConfirmationModal(false)}
        />
      )}
    </>
  );
};

PanelView.defaultProps = {
  node: undefined,
  links: undefined,
  link: undefined,
};
export default PanelView;
