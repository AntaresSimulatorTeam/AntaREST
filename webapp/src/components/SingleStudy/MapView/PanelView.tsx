import React, { useEffect, useState } from 'react';
import { ColorResult, HuePicker, MaterialPicker } from 'react-color';
import {
  makeStyles,
  createStyles,
  Theme,
  Typography,
  TextField,
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
      justifyContent: 'flex-end',
      alignItems: 'center',
      display: 'flex',
    },
    sliderpicker: {
      width: '100% !important',
      margin: theme.spacing(1),
    },
    materialpicker: {
      width: 'unset !important',
      maxWidth: '230px !important',
      fontFamily: '"Inter", sans-serif !important',
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
  const [currentColor, setCurrentColor] = useState<string>(node?.color || '');

  const handleChangeColor = (color: ColorResult) => {
    if (node) {
      setCurrentColor(`rgb(${color.rgb.r}, ${color.rgb.g}, ${color.rgb.b})`);
      // eslint-disable-next-line @typescript-eslint/camelcase
      onBlur(node.id, { x: node.x, y: node.y, color_rgb: color.rgb !== null ? [color.rgb.r, color.rgb.g, color.rgb.b] : node.color.slice(4, -1).split(',').map(Number) });
    }
  };

  useEffect(() => {
    if (node?.color) {
      setCurrentColor(node.color);
    }
  }, [node]);

  return (
    <>
      <div className={classes.form}>
        {node && (
          <>
            <TextField className={classes.fields} label={t('singlestudy:areaName')} variant="filled" value={node.id} disabled />
            <HuePicker className={classes.sliderpicker} color={currentColor} onChangeComplete={(color) => handleChangeColor(color)} />
            <MaterialPicker className={classes.materialpicker} color={currentColor} onChangeComplete={(color) => handleChangeColor(color)} />
            <TextField className={classes.fields} label={t('singlestudy:posX')} variant="filled" value={node.x} disabled />
            <TextField className={classes.fields} label={t('singlestudy:posY')} variant="filled" value={node.y} disabled />
          </>
        )}
        {links && node && (
          <LinksView links={links} node={node} onDelete={() => setOpenConfirmationModal(true)} />
        )}
        {link && (
        <>
          <Typography variant="body2" component="p">
            {link.source}
          </Typography>
          <Typography variant="body2" component="p">
            {link.target}
          </Typography>
          <div className={classes.buttons}>
            <DeleteIcon className={classes.deleteIcon} onClick={() => setOpenConfirmationModal(true)} />
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
