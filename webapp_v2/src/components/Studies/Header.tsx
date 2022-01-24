import React from 'react';
import { styled } from '@mui/material/styles';
import TravelExploreOutlinedIcon from '@mui/icons-material/TravelExploreOutlined';
import GetAppOutlinedIcon from '@mui/icons-material/GetAppOutlined';
import AddCircleOutlineOutlinedIcon from '@mui/icons-material/AddCircleOutlineOutlined';
import SearchOutlinedIcon from '@mui/icons-material/SearchOutlined';
import TextField from '@mui/material/TextField';
import { useTranslation } from 'react-i18next';
import { Box, Button, Divider, InputAdornment, Typography } from '@mui/material';

const Root = styled('div')(({ theme }) => ({
  width: '100%',
  height: 'auto',
  display: 'flex',
  flexFlow: 'column nowrap',
  justifyContent: 'flex-start',
  alignItems: 'center',
  boxSizing: 'border-box',
}));

const Searchbar = styled(TextField)(({ theme }) => ({
  color: theme.palette.grey[400],
  width: '400px',
  margin: theme.spacing(2),
  "& .MuiOutlinedInput-root": {
    backgroundColor: theme.palette.primary.dark,
    height: '40px',
    "&.Mui-focused fieldset": {
      borderColor: theme.palette.grey[400],
      color: theme.palette.grey[400]
    }
  }
}));

function Header() {
    const [t] = useTranslation();
  return (
    <Root>
        <Box width="100%" alignItems="center" display="flex" px={3}>
            <Box alignItems="center" display="flex">
                <TravelExploreOutlinedIcon sx={{ color: "grey.400", w: '32px', h: '32px' }} />
                <Typography color='white' sx={{ ml: 2, fontSize: '1.3em' }}>{t('main:studies')}</Typography>
            </Box>
            <Box alignItems="center" justifyContent="flex-end" flexGrow={1} display="flex">
                <Button variant="outlined" color="secondary" startIcon={<GetAppOutlinedIcon />}>
                    {t('main:import')}
                </Button>
                <Button sx={{ m: 2 }} variant="contained" color="secondary" startIcon={<AddCircleOutlineOutlinedIcon />}>
                    {t('main:create')}
                </Button>
            </Box>
        </Box>
        <Box display="flex" width="100%" alignItems="center" px={3}>
            <Box display="flex" width="100%" alignItems="center">
                <Searchbar
                    id="standard-basic"
                    placeholder={t('main:search')}
                    InputLabelProps={{
                        sx: { color: 'grey.400' },
                    }}
                    InputProps={{
                        startAdornment: (
                        <InputAdornment position="start">
                            <SearchOutlinedIcon sx={{ color: 'grey.400' }} />
                        </InputAdornment>
                        ),
                        sx: { color: 'grey.400' } }}/>
                <Divider style={{ width: '1px', height: '40px', backgroundColor: 'gray' }}/>
                <Button sx={{color:'primary.light', m: 2, borderStyle: "solid",  borderColor: 'primary.light' }} variant="outlined">
                    {t('main:filter')}
                </Button>
            </Box>
        </Box>
    </Root>   
  );
}

export default Header;
