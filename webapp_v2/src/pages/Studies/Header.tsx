import React, { CSSProperties } from 'react';
import { styled, useTheme } from '@mui/material/styles';
import TravelExploreOutlinedIcon from '@mui/icons-material/TravelExploreOutlined';
import GetAppOutlinedIcon from '@mui/icons-material/GetAppOutlined';
import AddCircleOutlineOutlinedIcon from '@mui/icons-material/AddCircleOutlineOutlined';
import SearchOutlinedIcon from '@mui/icons-material/SearchOutlined';
import TextField from '@mui/material/TextField';
import { useTranslation } from 'react-i18next';
import { Button, Divider, InputAdornment, Typography } from '@mui/material';

const Root = styled('div')(({ theme }) => ({
  width: '100%',
  height: 'auto',
  display: 'flex',
  flexFlow: 'column nowrap',
  justifyContent: 'flex-start',
  alignItems: 'center',
  boxSizing: 'border-box',
  //backgroundColor: 'red',
}));

function Header() {

    const theme = useTheme();
    const [t] = useTranslation();
    const style: CSSProperties = {
      width: '100%',
      //height: '40px',
      //backgroundColor: 'red',
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center'
    };
  return (
    <Root>
        <div style={{ ...style, padding: theme.spacing(0, 3) }}>
            <div style={style}>
                <TravelExploreOutlinedIcon sx={{ color: theme.palette.grey[400], width: '32px', height: '32px' }} />
                <Typography sx={{ color: 'white', margin: theme.spacing(0, 2), fontSize: '1.3em' }}>{t('main:studies')}</Typography>
            </div>
            <div style={{ flex: 1,
                          display: 'flex',
                          flexFlow: 'row nowrap',
                          justifyContent: 'flex-end',
                          alignItems: 'center' }}>
                <Button variant="outlined" color="secondary" startIcon={<GetAppOutlinedIcon />}>
                    {t('main:import')}
                </Button>
                <Button sx={{ margin: theme.spacing(2) }} variant="contained" color="secondary" startIcon={<AddCircleOutlineOutlinedIcon />}>
                    {t('main:create')}
                </Button>
            </div>
        </div>
        <div style={{ ...style, padding: theme.spacing(0, 3) }}>
            <div style={style}>
                <TextField
                    id="standard-basic"
                    label={t('main:search')}
                    sx={{ color: theme.palette.grey[400],
                          width: '400px',
                          minHeight: '40px',
                          margin: theme.spacing(2),
                          "& .MuiOutlinedInput-root": {
                            "&.Mui-focused fieldset": {
                              borderColor: theme.palette.grey[400],
                              color: theme.palette.grey[400]
                            }
                          },
                          "&.Mui-focused": {
                            color: "#23A5EB"
                          } }}
                          InputLabelProps={{
                              sx: { color: theme.palette.grey[400] },
                          }}
                    InputProps={{
                        startAdornment: (
                        <InputAdornment position="start">
                            <SearchOutlinedIcon sx={{ color: theme.palette.grey[400] }} />
                        </InputAdornment>
                        ),
                        sx: { color: theme.palette.grey[400] } }}/>
                <Divider style={{ width: '1px', height: '40px', background: theme.palette.grey[800] }}/>
                <Button sx={{ margin: theme.spacing(2), color: theme.palette.primary.light, border: `1px solid ${theme.palette.primary.light}` }} variant="outlined">
                    {t('main:filter')}
                </Button>
            </div>
        </div>
    </Root>   
  );
}

export default Header;
