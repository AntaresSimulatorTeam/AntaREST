import React, { useEffect, useState } from 'react';
import { ColorResult, HuePicker, MaterialPicker } from 'react-color';
import {
  Box,
  Typography,
  TextField,
  styled,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import DeleteIcon from '@mui/icons-material/Delete';
import { NodeProperties, LinkProperties, UpdateAreaUi } from '../../../../../common/types';
import BasicModal from '../../../../common/BasicModal';
import LinksView from './LinksView';

export const StyledDeleteIcon = styled(DeleteIcon)(({ theme }) => ({
  cursor: 'pointer',
  color: theme.palette.error.light,
  '&:hover': {
    color: theme.palette.error.main,
  },
}));

const StyledHuePicker = styled(HuePicker)(({ theme }) => ({
  width: '100% !important',
  margin: theme.spacing(1),
}));

const StyledMaterialPicker = styled(MaterialPicker)(({ theme }) => ({
  width: 'unset !important',
  maxWidth: '230px !important',
  fontFamily: '"Inter", sans-serif !important',
  boxShadow: 'none',
  border: '1px solid rgba(0,0,0,.12)',
}));

const StyledLinkTypo = styled(Typography)(({ theme }) => ({
  cursor: 'pointer',
  color: 'white',
  padding: theme.spacing(1),
  '&:hover': {
    textDecoration: 'underline',
  },
}));

interface PropType {
    node?: NodeProperties;
    nodes?: Array<NodeProperties>;
    links?: Array<LinkProperties>;
    link?: LinkProperties;
    onDelete: (id: string, target?: string) => void;
    updateUI: (id: string, value: UpdateAreaUi) => void;
    setSelectedItem: (item: NodeProperties | LinkProperties | undefined) => void;
}

function PanelView(props: PropType) {
  const [t] = useTranslation();
  const { node, nodes, links, link, onDelete, updateUI, setSelectedItem } = props;
  const [openConfirmationModal, setOpenConfirmationModal] = useState<boolean>(false);
  const [currentColor, setCurrentColor] = useState<string>(node?.color || '');

  const handleChangeColor = (color: ColorResult) => {
    if (node) {
      setCurrentColor(`rgb(${color.rgb.r}, ${color.rgb.g}, ${color.rgb.b})`);
      updateUI(node.id, { x: node.x, y: node.y, color_rgb: color.rgb !== null ? [color.rgb.r, color.rgb.g, color.rgb.b] : node.color.slice(4, -1).split(',').map(Number) });
    }
  };

  const handleClick = (name: string) => {
    if (nodes) {
      setSelectedItem(nodes.find((o) => o.id === name));
    }
  };

  useEffect(() => {
    if (node?.color) {
      setCurrentColor(node.color);
    }
  }, [node]);

  return (
    <>
      <Box width="94%" display="flex" justifyContent="flex-start" alignItems="center" flexDirection="column" padding="8px" flexGrow={1} marginBottom="76px">
        {node && (
          <>
            <TextField sx={{ mt: 1 }} label={t('singlestudy:areaName')} variant="filled" value={node.name} disabled />
            <TextField sx={{ mt: 1 }} label={t('singlestudy:posX')} variant="filled" value={node.x} disabled />
            <TextField sx={{ mt: 1 }} label={t('singlestudy:posY')} variant="filled" value={node.y} disabled />
            <StyledHuePicker color={currentColor} onChangeComplete={(color) => handleChangeColor(color)} />
            <StyledMaterialPicker color={currentColor} onChangeComplete={(color) => handleChangeColor(color)} />
          </>
        )}
        {links && node && (
          <LinksView links={links} node={node} onDelete={() => setOpenConfirmationModal(true)} setSelectedItem={setSelectedItem} />
        )}
        {link && (
        <Box width="100%" display="flex" flexDirection="column" alignItems="flex-start">
          <Typography sx={{ width: '90%', color: 'white', display: 'flex', flexFlow: 'row nowrap', justifyContent: 'flex-start', alignItems: 'center', boxSizing: 'border-box', textDecoration: 'underline', my: 1 }}>{t('singlestudy:link')}</Typography>
          <Box width="90%" display="flex" justifyContent="flex-start" alignItems="baseline" boxSizing="border-box" marginBottom="8px">
            <Typography sx={{ fontWeight: 'bold' }}>{t('singlestudy:area1')}</Typography>
            <StyledLinkTypo variant="body2" onClick={() => handleClick(link.source)}>
              {link.source}
            </StyledLinkTypo>
          </Box>
          <Box width="90%" display="flex" justifyContent="flex-start" alignItems="baseline" boxSizing="border-box" marginBottom="8px">
            <Typography sx={{ fontWeight: 'bold' }}>{t('singlestudy:area2')}</Typography>
            <StyledLinkTypo variant="body2" onClick={() => handleClick(link.target)}>
              {link.target}
            </StyledLinkTypo>
          </Box>
          <Box width="100%" display="flex" justifyContent="flex-end" alignItems="center">
            <StyledDeleteIcon onClick={() => setOpenConfirmationModal(true)} />
          </Box>
        </Box>
        )}

      </Box>
      {openConfirmationModal && node && (
        <BasicModal
          open={openConfirmationModal}
          title={t('main:confirmationModalTitle')}
          closeButtonLabel={t('main:noButton')}
          actionButtonLabel={t('main:yesButton')}
          onActionButtonClick={() => { onDelete(node.id); setOpenConfirmationModal(false); }}
          onClose={() => setOpenConfirmationModal(false)}
          rootStyle={{ display: 'flex', justifyContent: 'center', alignItems: 'center', overflowY: 'auto' }}
        >
          <Typography>
            {t('singlestudy:confirmDeleteArea')}
          </Typography>
        </BasicModal>
      )}
      {openConfirmationModal && link && (
        <BasicModal
          open={openConfirmationModal}
          title={t('main:confirmationModalTitle')}
          closeButtonLabel={t('main:noButton')}
          actionButtonLabel={t('main:yesButton')}
          onActionButtonClick={() => { onDelete(link.source, link.target); setOpenConfirmationModal(false); }}
          onClose={() => setOpenConfirmationModal(false)}
          rootStyle={{ display: 'flex', justifyContent: 'center', alignItems: 'center', overflowY: 'auto' }}
        >
          <Typography>
            {t('singlestudy:confirmDeleteLink')}
          </Typography>
        </BasicModal>
      )}
    </>
  );
}

PanelView.defaultProps = {
  nodes: undefined,
  node: undefined,
  links: undefined,
  link: undefined,
};
export default PanelView;
