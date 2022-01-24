import React, { PropsWithChildren } from 'react';
import { connect, ConnectedProps,  } from 'react-redux';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import CssBaseline from '@mui/material/CssBaseline';
import Toolbar from '@mui/material/Toolbar';
import List from '@mui/material/List';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
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

import { useTheme } from '@mui/material';
import logo from '../../assets/logo.png';
import { AppState } from '../../store/reducers';
import { setMenuExtensionStatusAction } from '../../store/ui';
import { CustomDrawer, CustomListItem, MenuLink, CustomNavLink, CustomListItemText, CustomListItemIcon} from '../../components/MenuWrapperComponents';


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

const MenuWrapper = (props: PropsWithChildren<PropTypes>) => {
    const { children, extended, setExtended } = props;
    const theme = useTheme();
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

    const drawMenuItem = (elm: MenuItem): JSX.Element => {
           
      return (<CustomListItem link key={elm.id}>
                {elm.newTab === true ?
                <MenuLink href={elm.link} target='_blank'>
                  <CustomListItemIcon>
                    {elm.icon({sx: { color: 'grey.400' }})}
                  </CustomListItemIcon>
                  {extended && <CustomListItemText primary={t(`main:${elm.id}`)} />}
                </MenuLink>:
                <CustomNavLink to={elm.link}
                      style={({isActive}) => ({
                              backgroundColor: isActive ? theme.palette.primary.dark :  undefined,})}>
                  <CustomListItemIcon>
                    {elm.icon({sx: { color: 'grey.400', }})}
                  </CustomListItemIcon>
                  {extended && <CustomListItemText primary={t(`main:${elm.id}`)} />}
                </CustomNavLink>}
              </CustomListItem>            
    )};

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <CustomDrawer
      extended={extended}
        variant="permanent"
        anchor="left"
      >
        <Toolbar>
          <Box display="flex" width="100%" height="100%" justifyContent={extended ? 'flex-start' : 'center'} alignItems="center" flexDirection="row" flexWrap="nowrap" boxSizing="border-box">
            <img src={logo} alt="logo" style={{ height: '32px', marginRight: extended ? '20px' : 0 }}/>
            {extended && <Typography style={{color: theme.palette.secondary.main, fontWeight: 'bold'}}>Antares Web</Typography>}
          </Box>
        </Toolbar>
        <Box display="flex" flex={1} justifyContent="space-between" flexDirection="column" sx={{ boxSizing: 'border-box'}}>
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
        </Box>
        <Divider style={{ height: '1px', backgroundColor: theme.palette.grey[800] }}/>
        <List>
            {drawMenuItem(settings)}
            <CustomListItem >
              <CustomListItemIcon>
                <AccountCircleOutlinedIcon sx={{ color: 'grey.400' }}/>
              </CustomListItemIcon>
              {extended && <CustomListItemText primary={t(`main:connexion`)} />}
            </CustomListItem>
            <CustomListItem onClick={() => setExtended(!extended)}>
              <CustomListItemIcon>
                {extended ? <FormatIndentDecreaseOutlinedIcon sx={{ color: 'grey.400' }}/>: <FormatIndentIncreaseOutlinedIcon sx={{ color: 'grey.400'  }}/>}
              </CustomListItemIcon>
              {extended && <CustomListItemText primary={t(`main:hide`)} />}
            </CustomListItem>
        </List>
      </CustomDrawer>
      <Box
        component="main"
        flexGrow={1}
        bgcolor="background.default"
        height="100vh"
      >
          {children}
      </Box>
    </Box>
  );
}

export default connector(MenuWrapper);