import React, { useState } from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
} from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import CloseIcon from '@material-ui/icons/Close';
import { NodeClickConfig, LinkClickConfig } from './types';
import ConfirmationModal from '../../ui/ConfirmationModal';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    header: {
      width: '100%',
      height: '40px',
      boxSizing: 'border-box',
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'space-between',
      alignItems: 'center',
      backgroundColor: theme.palette.primary.main,
      borderTopLeftRadius: theme.shape.borderRadius,
      borderTopRightRadius: theme.shape.borderRadius,
      paddingLeft: theme.spacing(2),
    },
    title: {
      fontWeight: 'bold',
      color: 'white',
    },
    popup: {
      position: 'absolute',
      right: '30px',
      top: '100px',
      width: '200px',
    },
    closeIcon: {
      color: 'white',
      marginLeft: theme.spacing(1),
      marginRight: theme.spacing(1),
      cursor: 'pointer',
    },
    buttons: {
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'space-between',
      alignItems: 'center',
    },
    deleteButton: {
      color: theme.palette.error.main,
      padding: theme.spacing(0),
      marginRight: theme.spacing(2),
      fontSize: '0.8em',
      '&:hover': {
        backgroundColor: '#0000',
      },
    },
  }));

interface PropType {
    name: string;
    node?: NodeClickConfig;
    link?: LinkClickConfig;
    onClose: () => void;
    onDelete: (id: string, target?: string) => void;
}

const PanelCardView = (props: PropType) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { name, node, link, onClose, onDelete } = props;
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);

  return (
    <>
      <Card className={classes.popup}>
        <Typography className={`${classes.header} ${classes.title}`} gutterBottom>
          {name}
          <CloseIcon className={classes.closeIcon} onClick={onClose} />
        </Typography>
        <CardContent>
          {node && (
            <>
              <Typography variant="h5" component="h2">
                {node.id}
              </Typography>
              <Typography variant="body2" component="p">
                {node.x}
                <br />
                {node.y}
                <br />
                {node.color}
              </Typography>
            </>
          )}
          {link && (
          <Typography variant="body2" component="p">
            {link.source}
            <br />
            {link.target}
          </Typography>
          )}
        </CardContent>
        <CardActions className={classes.buttons}>
          <Button size="small">{t('singlestudy:more')}</Button>
          {node && (
            <Button className={classes.deleteButton} onClick={() => setOpenConfirmationModal(true)} size="small">{t('main:delete')}</Button>
          )}
          {link && (
            <Button className={classes.deleteButton} onClick={() => setOpenConfirmationModal(true)} size="small">{t('main:delete')}</Button>
          )}
        </CardActions>
      </Card>
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

PanelCardView.defaultProps = {
  node: undefined,
  link: undefined,
};
export default PanelCardView;
