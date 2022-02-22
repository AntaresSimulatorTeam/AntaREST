import React, { useState } from 'react';
import { styled, useTheme } from '@mui/material/styles';
import TravelExploreOutlinedIcon from '@mui/icons-material/TravelExploreOutlined';
import AddCircleOutlineOutlinedIcon from '@mui/icons-material/AddCircleOutlineOutlined';
import SearchOutlinedIcon from '@mui/icons-material/SearchOutlined';
import TextField from '@mui/material/TextField';
import { useTranslation } from 'react-i18next';
import { Box, Button, Divider, InputAdornment, Typography, Chip } from '@mui/material';
import { STUDIES_HEIGHT_HEADER } from '../../theme';
import ImportStudy from './ImportStudy';
import CreateStudyModal from './CreateStudyModal';

const Root = styled('div')(({ theme }) => ({
  width: '100%',
  height: `${STUDIES_HEIGHT_HEADER}px`,
  display: 'flex',
  flexFlow: 'column nowrap',
  justifyContent: 'flex-start',
  alignItems: 'center',
  padding: theme.spacing(2, 0),
  boxSizing: 'border-box',
}));

const Searchbar = styled(TextField)(({ theme }) => ({
  color: theme.palette.grey[400],
  '& .MuiOutlinedInput-root': {
    height: '40px',
    '&.Mui-focused fieldset': {
    },
  },
}));

interface Props {
    inputValue: string;
    setInputValue: (value: string) => void;
    onFilterClick: () => void;
    managedFilter: boolean;
    setManageFilter: (value: boolean) => void;
}

function Header(props: Props) {
  const [t] = useTranslation();
  const theme = useTheme();
  const { inputValue, setInputValue, onFilterClick, managedFilter, setManageFilter } = props;
  const [openCreateModal, setOpenCreateModal] = useState<boolean>(false);

  const onActionButtonClick = () : void => {
    console.log('ACTION');
    setOpenCreateModal(false);
  };
  return (
    <Root>
      <Box width="100%" alignItems="center" display="flex" px={3}>
        <Box alignItems="center" display="flex">
          <TravelExploreOutlinedIcon sx={{ color: 'text.secondary', width: '42px', height: '42px' }} />
          <Typography color="white" sx={{ ml: 2, fontSize: '34px' }}>{t('main:studies')}</Typography>
        </Box>
        <Box alignItems="center" justifyContent="flex-end" flexGrow={1} display="flex">
          <ImportStudy />
          <Button sx={{ m: 2 }} variant="contained" color="primary" startIcon={<AddCircleOutlineOutlinedIcon />} onClick={() => setOpenCreateModal(true)}>
            {t('main:create')}
          </Button>
          {openCreateModal && <CreateStudyModal open={openCreateModal} onClose={() => setOpenCreateModal(false)} onActionButtonClick={onActionButtonClick} />}
        </Box>
      </Box>
      <Box display="flex" width="100%" alignItems="center" py={2} px={3}>
        <Box display="flex" width="100%" alignItems="center">
          <Searchbar
            id="standard-basic"
            value={inputValue}
            variant="outlined"
            sx={{ height: '40px' }}
            onChange={(event) => setInputValue(event.target.value as string)}
            label={t('main:search')}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchOutlinedIcon />
                </InputAdornment>
              ),
              sx: {
                '.MuiOutlinedInput-root': {
                  '&.MuiOutlinedInput-notchedOutline': {
                    borderColor: `${theme.palette.primary.main} !important`,
                  },
                },
                '.Mui-focused': {
                  //borderColor: `${theme.palette.primary.main} !important`
                },
                '.MuiOutlinedInput-notchedOutline': {
                  borderWidth: '1px',
                  borderColor: `${theme.palette.text.secondary} !important`,
                }
              } }}
              InputLabelProps={{
                sx: {
                  '.MuiInputLabel-root': {
                    color : theme.palette.text.secondary,
                  },
                  '.Mui-focused': {
                  }
                },
              }}

          />
          <Divider sx={{ width: '1px', height: '40px', bgcolor: 'divider', margin: '0px 16px' }} />
          <Button color="secondary" variant="outlined" onClick={onFilterClick}>
            {t('main:filter')}
          </Button>
          {
            managedFilter && (
            <Chip
              label={t('studymanager:managedStudiesFilter')}
              variant="filled"
              color="secondary"
              onDelete={() => setManageFilter(false)}
              sx={{ mx: 2 }}
            />
            )}
        </Box>
      </Box>
    </Root>
  );
}

export default Header;
