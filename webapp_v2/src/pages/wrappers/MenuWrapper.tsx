import React, { PropsWithChildren, useState } from 'react';
import { Link, useLinkClickHandler, useNavigate } from "react-router-dom";
import Box from '@mui/material/Box';
import Drawer from '@mui/material/Drawer';
import CssBaseline from '@mui/material/CssBaseline';
import Toolbar from '@mui/material/Toolbar';
import List from '@mui/material/List';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import ListItem from '@mui/material/ListItem';
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
import { styled, useTheme } from '@mui/material';
import logo from '../../assets/logo.png';

const drawerWidth = 60;
const drawerWidthExtended = 240;

const MenuLink = styled('a')(({ theme }) => ({
  color: 'white',
  outline: 0,
  textDecoration: 0,
  //backgroundColor: 'red',
}));

interface MenuItem {
  title: string;
  link: string;
  newTab?: boolean;
  icon: (props: any) => JSX.Element;
}


export default function PermanentDrawerLeft(props: PropsWithChildren<unknown>) {
    const { children } = props;
    const theme = useTheme();
    const navigate = useNavigate();
    const [extended, setExtended] = useState<boolean>(false);
  
    const menu: Array<MenuItem> = [{title: 'Studies', link: '/studies', icon: (props: any) => <TravelExploreOutlinedIcon {...props}/>},
                  {title: 'Data', link: '/data', icon: (props: any) => <ShowChartOutlinedIcon {...props}/>},
                  {title: 'Tasks', link: '/tasks', icon: (props: any) => <PlaylistAddCheckOutlinedIcon {...props}/>},
                ]
    const externalLink: Array<MenuItem> = [{title: 'API', link: '/api', icon: (props: any) => <ApiIcon {...props}/>},
                  {title: 'Documentation', link: 'https://antares-web.readthedocs.io/en/latest', newTab: true, icon: (props: any) => <ClassOutlinedIcon {...props}/>},
                  {title: 'Github', link: 'https://github.com/AntaresSimulatorTeam/AntaREST', newTab: true, icon: (props: any) => <GitHubIcon {...props}/>},
                ]
    const others: Array<MenuItem> = [{title: 'Connexion', link: '/connexions', icon: (props: any) => <AccountCircleOutlinedIcon {...props}/>},
                          {title: 'Settings', link: '/settings', icon: (props: any) => <SettingsOutlinedIcon {...props}/>},
                   ]
    const onMenuClick = (item: MenuItem) => {
      navigate(item.link);
    }

    const drawMenuItem = (elm: MenuItem): JSX.Element => (
      elm.newTab === true ?
      <MenuLink href={elm.link} target='_blank' style={{ width: '100%', height: '100%', display: 'flex', flexFlow: 'row nowrap', justifyContent: 'flex-start', alignItems: 'center' }}>
        <ListItemIcon>
          {elm.icon({style: { color: theme.palette.grey[400] }})}
        </ListItemIcon>
        {extended && <ListItemText primary={elm.title} style={{ color: 'white' }} />}
      </MenuLink>:
      <Link to={elm.link} style={{ width: '100%', height: '100%', display: 'flex', flexFlow: 'row nowrap', justifyContent: 'flex-start', alignItems: 'center', textDecoration: 0, outline: 0, color: 'white' }}>
        <ListItemIcon>
          {elm.icon({style: { color: theme.palette.grey[400] }})}
        </ListItemIcon>
        {extended && <ListItemText primary={elm.title} style={{ color: 'white' }} />}
     </Link>            
    )
    
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
          {menu.map((elm: MenuItem, index) => (
            <ListItem button key={elm.title}>
              {drawMenuItem(elm)}
            </ListItem>
          ))}
        </List>
        <List>
          {externalLink.map((elm: MenuItem, index) => (
            <ListItem button key={elm.title}>
              {drawMenuItem(elm)}
            </ListItem>
          ))}
        </List>
        </div>
        <Divider style={{ height: '1px', background: theme.palette.grey[800] }}/>
        <List>
          {others.map((elm, index) => (
            <ListItem button key={elm.title}>
              {drawMenuItem(elm)}
            </ListItem>
          ))}
          <ListItem button onClick={() => setExtended(!extended)}>
            <ListItemIcon>
              {extended ? <FormatIndentDecreaseOutlinedIcon style={{ color: theme.palette.grey[400] }}/>: <FormatIndentIncreaseOutlinedIcon style={{ color: theme.palette.grey[400] }}/>}
            </ListItemIcon>
            {extended && <ListItemText primary="Mask" style={{ color: 'white' }} />}
          </ListItem>
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
