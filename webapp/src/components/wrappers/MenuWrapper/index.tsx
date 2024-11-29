/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import { FunctionComponent, ReactNode, useState } from "react";
import { useTranslation } from "react-i18next";
import { NavLink } from "react-router-dom";
import Box from "@mui/material/Box";
import CssBaseline from "@mui/material/CssBaseline";
import Toolbar from "@mui/material/Toolbar";
import List from "@mui/material/List";
import Typography from "@mui/material/Typography";
import Divider from "@mui/material/Divider";
import TravelExploreOutlinedIcon from "@mui/icons-material/TravelExploreOutlined";
import StorageIcon from "@mui/icons-material/Storage";
import AssignmentIcon from "@mui/icons-material/Assignment";
import CenterFocusStrongIcon from "@mui/icons-material/CenterFocusStrong";
import ApiIcon from "@mui/icons-material/Api";
import ClassOutlinedIcon from "@mui/icons-material/ClassOutlined";
import GitHubIcon from "@mui/icons-material/GitHub";
import LogoutIcon from "@mui/icons-material/Logout";
import SettingsOutlinedIcon from "@mui/icons-material/SettingsOutlined";
import ArrowForwardIosIcon from "@mui/icons-material/ArrowForwardIos";
import ArrowBackIosIcon from "@mui/icons-material/ArrowBackIos";
import {
  keyframes,
  styled,
  SvgIconProps,
  Tooltip,
  useTheme,
} from "@mui/material";
import { useMount } from "react-use";
import logo from "../../../assets/img/logo.png";
import NotificationBadge from "../../App/Tasks/NotificationBadge";
import topRightBackground from "../../../assets/img/top-right-background.png";
import { setMenuCollapse } from "../../../redux/ducks/ui";
import {
  NavDrawer,
  NavListItem,
  NavExternalLink,
  NavInternalLink,
  NavListItemText,
  NavListItemIcon,
  Root,
  TootlbarContent,
  MenuContainer,
  LogoContainer,
} from "./styles";
import { getConfig } from "../../../services/config";
import {
  getCurrentStudyId,
  getMenuExtended,
  getWebSocketConnected,
} from "../../../redux/selectors";
import ConfirmationDialog from "../../common/dialogs/ConfirmationDialog";
import { logout } from "../../../redux/ducks/auth";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import { fetchUsers } from "../../../redux/ducks/users";
import { fetchGroups } from "../../../redux/ducks/groups";

const pulsatingAnimation = keyframes`
  0% {
    opacity: 1
  }
  50% {
    opacity: 0
  }
  100% {
    opacity: 1
  }
`;

const BorderedPulsating = styled("div")(({ theme }) => ({
  "&::before": {
    content: '""',
    position: "absolute",
    width: "32px",
    border: `1px solid ${theme.palette.secondary.main}`,
    borderRadius: "50%",
    height: "32px",
    animation: `${pulsatingAnimation} 2s infinite`,
    boxShadow: `0 0px 10px 0 ${theme.palette.secondary.main}`,
  },
}));

interface MenuItem {
  id: string;
  link: string;
  newTab?: boolean;
  strict?: boolean;
  icon: FunctionComponent<SvgIconProps>;
}

interface Props {
  children: ReactNode;
}

function MenuWrapper(props: Props) {
  const { children } = props;
  const theme = useTheme();
  const [t] = useTranslation();
  const [openLogoutDialog, setOpenLogoutDialog] = useState<boolean>(false);
  const versionInfo = getConfig().version;
  const extended = useAppSelector(getMenuExtended);
  const currentStudy = useAppSelector(getCurrentStudyId);
  const websocketConnected = useAppSelector(getWebSocketConnected);
  const dispatch = useAppDispatch();

  useMount(() => {
    dispatch(fetchUsers());
    dispatch(fetchGroups());
  });

  let navigation: MenuItem[] = [
    {
      id: "studies.title",
      link: "/studies",
      strict: true,
      icon: TravelExploreOutlinedIcon,
    },
    { id: "tasks.title", link: "/tasks", icon: AssignmentIcon },
    { id: "data.title", link: "/data", icon: StorageIcon },
    { id: "api.title", link: "/apidoc", icon: ApiIcon },
    {
      id: "documentation.title",
      link: "https://antares-doc.readthedocs.io/en/latest",
      newTab: true,
      icon: ClassOutlinedIcon,
    },
    {
      id: "github.title",
      link: "https://github.com/AntaresSimulatorTeam/AntaREST",
      newTab: true,
      icon: GitHubIcon,
    },
    { id: "settings.title", link: "/settings", icon: SettingsOutlinedIcon },
  ];

  if (currentStudy) {
    navigation = (
      [
        {
          id: "recentStudy.title",
          link: `/studies/${currentStudy}`,
          icon: CenterFocusStrongIcon,
        },
      ] as MenuItem[]
    ).concat(navigation);
  }

  const settings = navigation[navigation.length - 1];

  const drawMenuItem = (elm: MenuItem): ReactNode => {
    const tooltipTitle = extended ? "" : t(elm.id);

    if (elm.id === "tasks.title") {
      return (
        <Tooltip title={tooltipTitle} placement="right-end" key={elm.id}>
          <NavListItem link>
            <NavInternalLink
              to={elm.link}
              end={elm.strict}
              style={({ isActive }) => ({
                background: isActive
                  ? theme.palette.primary.outlinedHoverBackground
                  : undefined,
              })}
            >
              <NotificationBadge>
                <NavListItemIcon>
                  <elm.icon sx={{ color: "grey.400" }} />
                </NavListItemIcon>
              </NotificationBadge>
              {extended && <NavListItemText primary={t(`${elm.id}`)} />}
            </NavInternalLink>
          </NavListItem>
        </Tooltip>
      );
    }
    return (
      <NavListItem link key={elm.id}>
        <Tooltip title={tooltipTitle} placement="right-end">
          {elm.newTab === true ? (
            <NavExternalLink href={elm.link} target="_blank">
              <NavListItemIcon>
                <elm.icon sx={{ color: "grey.400" }} />
              </NavListItemIcon>
              {extended && <NavListItemText primary={t(`${elm.id}`)} />}
            </NavExternalLink>
          ) : (
            <NavInternalLink
              to={elm.link}
              end={elm.strict}
              style={({ isActive }) => ({
                background: isActive
                  ? theme.palette.primary.outlinedHoverBackground
                  : undefined,
              })}
            >
              <NavListItemIcon>
                <elm.icon sx={{ color: "grey.400" }} />
              </NavListItemIcon>
              {extended && <NavListItemText primary={t(`${elm.id}`)} />}
            </NavInternalLink>
          )}
        </Tooltip>
      </NavListItem>
    );
  };

  const topMenuLastIndexOffset = currentStudy ? 1 : 0;

  return (
    <Root>
      <CssBaseline />
      <LogoContainer>
        <img src={topRightBackground} alt="logo" style={{ height: "auto" }} />
      </LogoContainer>
      <NavDrawer extended={extended} variant="permanent" anchor="left">
        <Toolbar>
          <TootlbarContent extended={extended}>
            <NavLink to="/">
              {websocketConnected ? (
                <img
                  src={logo}
                  alt="logo"
                  style={{
                    height: "32px",
                    marginRight: extended ? "20px" : 0,
                    marginTop: "18px",
                  }}
                />
              ) : (
                <BorderedPulsating
                  style={{
                    marginRight: extended ? "20px" : 0,
                    marginTop: "18px",
                  }}
                >
                  <img src={logo} alt="logo" style={{ height: "32px" }} />
                </BorderedPulsating>
              )}
            </NavLink>
            {extended && (
              <Tooltip
                title={`${versionInfo.version} (${versionInfo.gitcommit})`}
              >
                <Typography
                  style={{
                    color: theme.palette.secondary.main,
                    fontWeight: "bold",
                    marginTop: "12px",
                  }}
                >
                  Antares Web
                </Typography>
              </Tooltip>
            )}
          </TootlbarContent>
        </Toolbar>
        <MenuContainer>
          <List>
            {navigation
              .slice(0, 3 + topMenuLastIndexOffset)
              .map((elm: MenuItem, index) => drawMenuItem(elm))}
          </List>
          <List>
            {navigation
              .slice(3 + topMenuLastIndexOffset, 6 + topMenuLastIndexOffset)
              .map((elm: MenuItem, index) => drawMenuItem(elm))}
          </List>
        </MenuContainer>
        <Divider />
        <List>
          {drawMenuItem(settings)}
          <Tooltip
            title={t(extended ? "" : "logout.title")}
            placement="right-end"
          >
            <NavListItem onClick={() => setOpenLogoutDialog(true)}>
              <NavInternalLink to="#">
                <NavListItemIcon sx={{ color: "grey.400" }}>
                  <LogoutIcon />
                </NavListItemIcon>
                {extended && <NavListItemText primary={t("logout.title")} />}
              </NavInternalLink>
            </NavListItem>
          </Tooltip>
          <Tooltip
            title={t(extended ? "" : "button.expand")}
            placement="right-end"
          >
            <NavListItem onClick={() => dispatch(setMenuCollapse(extended))}>
              <NavInternalLink to="#">
                <NavListItemIcon sx={{ color: "grey.400" }}>
                  {extended ? <ArrowBackIosIcon /> : <ArrowForwardIosIcon />}
                </NavListItemIcon>
                {extended && <NavListItemText primary={t("button.collapse")} />}
              </NavInternalLink>
            </NavListItem>
          </Tooltip>
        </List>
        {openLogoutDialog && (
          <ConfirmationDialog
            title={t("logout.title")}
            onCancel={() => setOpenLogoutDialog(false)}
            onConfirm={() => dispatch(logout())}
            alert="warning"
            open
          >
            <Typography sx={{ px: 3, py: 1 }}>
              {t("dialog.message.logout")}
            </Typography>
          </ConfirmationDialog>
        )}
      </NavDrawer>
      <Box
        component="main"
        flexGrow={1}
        bgcolor="inherit"
        height="100vh"
        overflow="hidden"
        zIndex={1}
      >
        {children}
      </Box>
    </Root>
  );
}

export default MenuWrapper;
