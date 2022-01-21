import React, { useState } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  Typography,
  TextField,
} from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import { NodeProperties, LinkProperties } from './types';
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
    },
    fields: {
      marginTop: theme.spacing(1),
    },
  }));

interface PropType {
    node?: NodeProperties;
    links?: Array<LinkProperties>;
    link?: LinkProperties;
    onDelete: (id: string, target?: string) => void;
}

const PanelView = (props: PropType) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { node, links, link, onDelete } = props;
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);

  return (
    <>
      <div className={classes.form}>
        {node && (
          <>
            <TextField className={classes.fields} label={t('singlestudy:areaName')} variant="filled" value={node.id} disabled />
            <TextField className={classes.fields} label={t('singlestudy:color')} variant="filled" value={node.color} />
            <TextField className={classes.fields} label={t('singlestudy:posX')} variant="filled" value={node.x} />
            <TextField className={classes.fields} label={t('singlestudy:posY')} variant="filled" value={node.y} />
          </>
        )}
        {links && node && (
          <LinksView links={links} node={node} />
        )}
        {link && (
        <Typography variant="body2" component="p">
          {link.source}
          <br />
          {link.target}
        </Typography>
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
