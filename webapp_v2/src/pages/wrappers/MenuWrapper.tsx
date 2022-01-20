import React, { CSSProperties, PropsWithChildren, useEffect, useState } from 'react';
import { Link, NavLink, useLocation } from "react-router-dom";
import { connect, ConnectedProps,  } from 'react-redux';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Drawer from '@mui/material/Drawer';
import CssBaseline from '@mui/material/CssBaseline';
import Toolbar from '@mui/material/Toolbar';
import List from '@mui/material/List';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import ListItem, { ListItemProps } from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import TravelExploreOutlinedIcon from '@mui/icons-material/TravelExploreOutlined';
import ShowChartOutlinedIcon from '@mui/icons-material/ShowChartOutlined';
import PlaylistAddCheckOutlinedIcon from '@mui/icons-material/PlaylistAddCheckOutlined';

import ApiIcon from '@mui/icons-material/Api';
import ClassOutlinedIcon from '@mui/icons-material/ClassOutlined';
import GitHubIcon from '@mui/icons-material/GitHub';

import AccountCircleOutlinedIcon from '@mui/icons-material/AccountCircleOutlined';
import SettingsOutlinedIcon from '@mui/icons-material/SettingsOutlined';
import FormatIndentIncreaseOutlinedIcon from '@mui/icons-material/FormatIndentIncreaseOutlined';
import FormatIndentDecreaseOutlinedIcon from '@mui/icons-material/FormatIndentDecreaseOutlined';

import { styled, SxProps, Theme, useTheme } from '@mui/material';
import logo from '../../assets/logo.png';
import { AppState } from '../../store/reducers';
import { setMenuExtensionStatusAction } from '../../store/ui';

const drawerWidth = 60;
const drawerWidthExtended = 240;

const MenuLink = styled('a')(({ theme }) => ({
  color: 'white',
  outline: 0,
  textDecoration: 0,
}));

const CustomListItem = styled(ListItem)<ListItemProps>(({ theme }) => ({
  cursor: 'pointer',
  width: '100%',
  height: '60px',
  padding: 0,
  '&:hover': {
    backgroundColor: theme.palette.primary.dark,
  },
}));

interface MenuItem {
  id: string;
  link: string;
  newTab?: boolean;
  icon: (props: any) => JSX.Element;
}

const mapState = (state: AppState) => ({
  extended: state.ui.menuExtended,
});

const mapDispatch = ({
  setExtended: setMenuExtensionStatusAction,
});

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const PermanentDrawerLeft = (props: PropsWithChildren<PropTypes>) => {
    const { children, extended, setExtended } = props;
    const theme = useTheme();
    const location = useLocation();
    const [t] = useTranslation();

    const navigation: Array<MenuItem> = [
      {id: 'studies', link: '/studies', icon: (props: any) => <TravelExploreOutlinedIcon {...props}/>,},
      {id: 'data', link: '/data', icon: (props: any) => <ShowChartOutlinedIcon {...props}/>},
      {id: 'tasks', link: '/tasks', icon: (props: any) => <PlaylistAddCheckOutlinedIcon {...props}/>},
      {id: 'api', link: '/api', icon: (props: any) => <ApiIcon {...props}/>},
      {id: 'documentation', link: 'https://antares-web.readthedocs.io/en/latest', newTab: true, icon: (props: any) => <ClassOutlinedIcon {...props}/>},
      {id: 'github', link: 'https://github.com/AntaresSimulatorTeam/AntaREST', newTab: true, icon: (props: any) => <GitHubIcon {...props}/>},
      {id: 'settings', link: '/settings', icon: (props: any) => <SettingsOutlinedIcon {...props}/>}
  ];

  const settings = navigation[navigation.length -1];

  const linkStyle: CSSProperties = {
    width: '100%',
    height: '100%',
    display: 'flex',
    padding: theme.spacing(1, 1),
    flexFlow: extended ? 'row nowrap' : 'column nowrap',
    justifyContent: extended ? 'flex-start' : 'center',
    alignItems: 'center',
    boxSizing: 'border-box',
    textDecoration: 0,
    outline: 0};
  const iconStyle: CSSProperties = {
    width: extended ? 'auto': '100%',
    display: 'flex',
    justifyContent: 'center'};
  const textStyle: SxProps<Theme> = {
    color: theme.palette.grey[400],
    '& span, & svg': {
      fontSize: extended ? '0.8em': '0.48em',
      fontWeight: 'bold',
    }}; 

    const drawMenuItem = (elm: MenuItem): JSX.Element => {
           
      return (<CustomListItem key={elm.id}>
                {elm.newTab === true ?
                <MenuLink href={elm.link} target='_blank' sx={linkStyle}>
                  <ListItemIcon sx={iconStyle}>
                    {elm.icon({style: { color: theme.palette.grey[400] }})}
                  </ListItemIcon>
                  <ListItemText primary={t(`main:${elm.id}`)} sx={textStyle} />
                </MenuLink>:
                <NavLink to={elm.link}
                      style={({isActive}) => ({...linkStyle,
                              backgroundColor: isActive ? theme.palette.primary.dark :  undefined,
                              borderRight: isActive ? `4px solid ${theme.palette.primary.light}`: 0,})}>
                  <ListItemIcon sx={iconStyle}>
                    {elm.icon({sx: { color: theme.palette.grey[400], }})}
                  </ListItemIcon>
                  <ListItemText primary={t(`main:${elm.id}`)} sx={textStyle} />
                </NavLink>}
              </CustomListItem>            
    )};

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <Drawer
        sx={{
          width: extended ? drawerWidthExtended: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: extended ? drawerWidthExtended: drawerWidth,
            boxSizing: 'border-box',
            overflow: 'hidden',
            backgroundColor: theme.palette.primary.main,
            borderRight: `1px solid ${theme.palette.grey[800]}`,
          },
        }}
        variant="permanent"
        anchor="left"
      >
        <Toolbar>
          <div style={{display: 'flex', width: '100%', height: '100%', flexFlow: 'row nowrap', boxSizing: 'border-box', justifyContent: extended ? 'flex-start' : 'center', alignItems: 'center'}}>
            <img src={logo} alt="logo" style={{ height: '32px', marginRight: extended ? '20px' : 0 }}/>
            {extended && <Typography style={{color: theme.palette.secondary.main, fontWeight: 'bold'}}>Antares Web</Typography>}
          </div>
        </Toolbar>
        <Divider style={{ height: '1px', background: theme.palette.grey[800] }}/>
        <div style={{display: 'flex', flex: 1, flexFlow: 'column nowrap', boxSizing: 'border-box', justifyContent: 'space-between'}}>
        <List>
          {navigation.slice(0, 3).map((elm: MenuItem, index) => (
              drawMenuItem(elm)
          ))}
        </List>
        <List>
          {navigation.slice(3, 6).map((elm: MenuItem, index) => (
              drawMenuItem(elm)
          ))}
        </List>
        </div>
        <Divider style={{ height: '1px', background: theme.palette.grey[800] }}/>
        <List>
            {drawMenuItem(settings)}
            <CustomListItem sx={{ 
                              padding: extended ? theme.spacing(1, 1): 0,
                              width: '100%',
                              display: 'flex',
                              flexFlow: 'row nowrap',
                              justifyContent: 'flex-start',
                              alignItems: 'center',
                              boxSizing: 'border-box'}}>
              <ListItemIcon sx={iconStyle}>
              <AccountCircleOutlinedIcon style={{ color: theme.palette.grey[400] }}/>
             </ListItemIcon>
              <ListItemText primary={t(`main:connexion`)} sx={textStyle} />
            </CustomListItem>
            <CustomListItem onClick={() => setExtended(!extended)} sx={{ 
                              padding: extended ? theme.spacing(1, 1): 0,
                              width: '100%',
                              display: 'flex',
                              flexFlow: 'row nowrap',
                              justifyContent: 'flex-start',
                              alignItems: 'center',
                              boxSizing: 'border-box'}}>
            <ListItemIcon sx={iconStyle}>
              {extended ? <FormatIndentDecreaseOutlinedIcon style={{ color: theme.palette.grey[400] }}/>: <FormatIndentIncreaseOutlinedIcon style={{ color: theme.palette.grey[400]  }}/>}
            </ListItemIcon>
            {extended && <ListItemText primary={t(`main:hide`)} sx={textStyle} />}
          </CustomListItem>
        </List>
      </Drawer>
      <Box
        component="main"
        sx={{ flexGrow: 1, bgcolor: 'background.default', p: 0, height: '100vh'}}
      >
          {children}
      </Box>
    </Box>
  );
}

export default connector(PermanentDrawerLeft);