/* eslint-disable react/jsx-props-no-spreading */
import {
  FunctionComponent,
  PropsWithChildren,
  ReactNode,
  useState,
} from "react";
import { connect, ConnectedProps } from "react-redux";
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
import ReadMoreOutlinedIcon from "@mui/icons-material/ReadMoreOutlined";

import {
  keyframes,
  styled,
  SvgIconProps,
  Tooltip,
  useTheme,
} from "@mui/material";
import logo from "../../../assets/logo.png";
import NotificationBadge from "../../../components/tasks/NotificationBadge";
import topRightBackground from "../../../assets/top-right-background.png";
import { AppState } from "../../../redux/ducks";
import { setMenuExtensionStatus } from "../../../redux/ducks/ui";
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
import ConfirmationDialog from "../../../components/common/dialogs/ConfirmationDialog";
import { logoutAction } from "../../../store/auth";

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

const mapState = (state: AppState) => ({
  extended: state.ui.menuExtended,
  currentStudy: state.study.current,
  websocketConnected: state.websockets.connected,
});

const mapDispatch = {
  setExtended: setMenuExtensionStatus,
  logout: logoutAction,
};

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

function MenuWrapper(props: PropsWithChildren<PropTypes>) {
  const {
    children,
    extended,
    setExtended,
    logout,
    currentStudy,
    websocketConnected,
  } = props;
  const theme = useTheme();
  const [t] = useTranslation();
  const [openLogoutDialog, setOpenLogoutDialog] = useState<boolean>(false);
  const versionInfo = getConfig().version;

  let navigation: Array<MenuItem> = [
    {
      id: "studies",
      link: "/studies",
      strict: true,
      icon: TravelExploreOutlinedIcon,
    },
    { id: "tasks", link: "/tasks", icon: AssignmentIcon },
    { id: "data", link: "/data", icon: StorageIcon },
    { id: "api", link: "/apidoc", icon: ApiIcon },
    {
      id: "documentation",
      link: "https://antares-web.readthedocs.io/en/latest",
      newTab: true,
      icon: ClassOutlinedIcon,
    },
    {
      id: "github",
      link: "https://github.com/AntaresSimulatorTeam/AntaREST",
      newTab: true,
      icon: GitHubIcon,
    },
    { id: "settings", link: "/settings", icon: SettingsOutlinedIcon },
  ];

  if (currentStudy) {
    navigation = (
      [
        {
          id: "recentStudy",
          link: `/studies/${currentStudy}`,
          icon: CenterFocusStrongIcon,
        },
      ] as MenuItem[]
    ).concat(navigation);
  }

  const settings = navigation[navigation.length - 1];

  const drawMenuItem = (elm: MenuItem): ReactNode => {
    if (elm.id === "tasks") {
      return (
        <NavListItem link key={elm.id}>
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
            {extended && <NavListItemText primary={t(`main:${elm.id}`)} />}
          </NavInternalLink>
        </NavListItem>
      );
    }
    return (
      <NavListItem link key={elm.id}>
        {elm.newTab === true ? (
          <NavExternalLink href={elm.link} target="_blank">
            <NavListItemIcon>
              <elm.icon sx={{ color: "grey.400" }} />
            </NavListItemIcon>
            {extended && <NavListItemText primary={t(`main:${elm.id}`)} />}
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
            {extended && <NavListItemText primary={t(`main:${elm.id}`)} />}
          </NavInternalLink>
        )}
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
          <NavListItem onClick={() => setOpenLogoutDialog(true)}>
            <NavListItemIcon>
              <LogoutIcon sx={{ color: "grey.400" }} />
            </NavListItemIcon>
            {extended && <NavListItemText primary={t("main:logout")} />}
          </NavListItem>
          <NavListItem onClick={() => setExtended(!extended)}>
            <NavListItemIcon>
              <ReadMoreOutlinedIcon sx={{ color: "grey.400" }} />
            </NavListItemIcon>
            {extended && <NavListItemText primary={t("main:hide")} />}
          </NavListItem>
        </List>
        {openLogoutDialog && (
          <ConfirmationDialog
            title={t("main:logout")}
            onCancel={() => setOpenLogoutDialog(false)}
            onConfirm={logout}
            alert="warning"
            open
          >
            {t("main:logoutModalMessage")}
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

export default connector(MenuWrapper);
