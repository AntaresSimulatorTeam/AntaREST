import React, { CSSProperties, PropsWithChildren } from 'react';
import { NavLink } from "react-router-dom";
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
import { DRAWER_WIDTH, DRAWER_WIDTH_EXTENDED } from '../theme';


export const MenuLink = styled('a')(({
  color: 'white',
  width: '100%',
  height: '100%',
  display: 'flex',
  padding: 0,
  flexFlow: 'row nowrap',
  justifyContent: 'flex-end',
  alignItems: 'center',
  boxSizing: 'border-box',
  textDecoration: 0,
  outline: 0
}));


export const CustomListItem = styled(ListItem, { shouldForwardProp: (prop) => prop !== 'link'})<{link?: boolean, extended?: boolean}> (({ theme, link }) => ({
  cursor: 'pointer',
  width: '100%',
  height: '60px',
  padding: 0,
  margin: theme.spacing(1, 0),
  boxSizing: 'border-box',
  '&:hover': {
    backgroundColor: theme.palette.primary.dark,
  },
  ...(!link && { display: 'flex',
  flexFlow: 'row nowrap',
  justifyContent: 'flex-start',
  alignItems: 'center' })
}));

export const CustomNavLink = styled(NavLink)(({
    width: '100%',
    height: '100%',
    display: 'flex',
    padding: 0,
    flexFlow: 'row nowrap',
    justifyContent: 'flex-end',
    alignItems: 'center',
    boxSizing: 'border-box',
    textDecoration: 0,
    outline: 0
}));

export const CustomListItemText = styled(ListItemText)(({ theme }) => ({
    color: theme.palette.grey[400],
    '& span, & svg': {
      fontSize: '0.8em',
    }
  }));
  
  export const CustomListItemIcon = styled(ListItemIcon)(({
    width: 'auto',
    display: 'flex',
    boxSizing: 'border-box',
    justifyContent: 'center'
  }));


const options = {
    shouldForwardProp: (propName: PropertyKey) => propName !== 'extended',  
};

  export const CustomDrawer = styled(Drawer, options)<{extended?: boolean}>(({ theme, extended }) => ({
    width: extended ? DRAWER_WIDTH_EXTENDED: DRAWER_WIDTH,
    flexShrink: 0,
    '& .MuiDrawer-paper': {
      width: extended ? DRAWER_WIDTH_EXTENDED: DRAWER_WIDTH,
      boxSizing: 'border-box',
      overflow: 'hidden',
      backgroundColor: theme.palette.primary.main,
      borderRight: `1px solid ${theme.palette.grey[800]}`,
    },
  }));

export default {};