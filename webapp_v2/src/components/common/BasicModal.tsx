import React, { PropsWithChildren } from 'react';
import { useTranslation } from 'react-i18next';
import { SxProps, Box, Button, Typography, Modal, Paper, Theme } from '@mui/material';

const style = {
  position: 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: 400,
  bgcolor: 'background.paper',
  border: '2px solid #000',
  boxShadow: 24,
  p: 4,
};

interface Props {
    title: string;
    open: boolean;
    onClose: () => void;
    closeButtonLabel?: string;
    actionButtonLabel?: string;
    onActionButtonClick: () => void;
    rootStyle?: SxProps<Theme> | undefined;
}

function BasicModal(props: PropsWithChildren<Props>) {
  const { title, open, onClose, closeButtonLabel, actionButtonLabel, onActionButtonClick, rootStyle, children } = props;
  const [t] = useTranslation();

  return (
    <Modal
      open={open}
      aria-labelledby={`modal-label-${title}`}
      aria-describedby={`modal-description-${title}`}
      sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', bgcolor: '#0000', boxSizing: 'border-box' }}
    >
      <Paper sx={rootStyle}>
        <Box width="100%" height="64px" display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center" py={2} px={3} boxSizing="border-box">
          <Typography sx={{ color: 'white', fontWeight: 500, fontSize: '20px', boxSizing: 'border-box' }}>{title}</Typography>
        </Box>
        <Box width="100%" flexGrow={1} display="flex" flexDirection="column" justifyContent="center" alignItems="center" p={0} boxSizing="border-box">
          {children}
        </Box>
        <Box width="100%" height="64px" display="flex" flexDirection="row" justifyContent="flex-end" alignItems="center" p={2} boxSizing="border-box">
          <Button variant="text" color="error" onClick={onClose}>
            {closeButtonLabel !== undefined ? closeButtonLabel : t('main:closeButton')}
          </Button>
          <Button sx={{ mx: 2 }} color="success" variant="contained" onClick={onActionButtonClick}>
            {actionButtonLabel !== undefined ? actionButtonLabel : t('main:save')}
          </Button>
        </Box>
      </Paper>
    </Modal>
  );
}

BasicModal.defaultProps = {
  closeButtonLabel: undefined,
  actionButtonLabel: undefined,
};

export default BasicModal;
