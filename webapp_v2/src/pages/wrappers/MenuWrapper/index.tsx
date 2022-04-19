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

import { SvgIconProps, useTheme } from "@mui/material";
import logo from "../../../assets/logo.png";
import DownloadBadge from "../../../components/tasks/DownloadBadge";
import topRightBackground from "../../../assets/top-right-background.png";
import { AppState } from "../../../store/reducers";
import { setMenuExtensionStatusAction } from "../../../store/ui";
import {
  NavDrawer,
  NavListItem,
  NavExternalLink,
  NavInternalLink,
  NavListItemText,
  NavListItemIcon,
} from "../../../components/MenuWrapperComponents";
import LogoutModal from "./LogoutModal";

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
  setExtended: setMenuExtensionStatusAction,
};

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

function MenuWrapper(props: PropsWithChildren<PropTypes>) {
  const { children, extended, setExtended, currentStudy } = props;
  const theme = useTheme();
  const [t] = useTranslation();
  const [openLogoutModal, setOpenLogoutModal] = useState<boolean>(false);

  let navigation: Array<MenuItem> = [
    {
      id: "studies",
      link: "/studies",
      strict: true,
      icon: TravelExploreOutlinedIcon,
    },
    { id: "tasks", link: "/tasks", icon: AssignmentIcon },
    { id: "data", link: "/data", icon: StorageIcon },
    { id: "api", link: "/api", icon: ApiIcon },
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
            <DownloadBadge>
              <NavListItemIcon>
                <elm.icon sx={{ color: "grey.400" }} />
              </NavListItemIcon>
            </DownloadBadge>
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
    <Box
      display="flex"
      width="100vw"
      height="100vh"
      overflow="hidden"
      sx={{
        background:
          "radial-gradient(ellipse at top right, #190520 0%, #190520 30%, #222333 100%)",
      }}
    >
      <CssBaseline />
      <Box
        position="absolute"
        top="0px"
        right="0px"
        display="flex"
        justifyContent="center"
        alignItems="center"
        flexDirection="column"
        flexWrap="nowrap"
        boxSizing="border-box"
      >
        <img src={topRightBackground} alt="logo" style={{ height: "auto" }} />
      </Box>
      <NavDrawer extended={extended} variant="permanent" anchor="left">
        <Toolbar>
          <Box
            display="flex"
            width="100%"
            height="100%"
            justifyContent={extended ? "flex-start" : "center"}
            alignItems="center"
            flexDirection="row"
            flexWrap="nowrap"
            boxSizing="border-box"
          >
            <NavLink to={navigation[0].link}>
              <img
                src={logo}
                alt="logo"
                style={{ height: "32px", marginRight: extended ? "20px" : 0 }}
              />
            </NavLink>
            {extended && (
              <Typography
                style={{
                  color: theme.palette.secondary.main,
                  fontWeight: "bold",
                }}
              >
                Antares Web
              </Typography>
            )}
          </Box>
        </Toolbar>
        <Box
          display="flex"
          flex={1}
          justifyContent="space-between"
          flexDirection="column"
          sx={{ boxSizing: "border-box" }}
        >
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
        </Box>
        <Divider />
        <List>
          {drawMenuItem(settings)}
          <NavListItem onClick={() => setOpenLogoutModal(true)}>
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
        {openLogoutModal && (
          <LogoutModal
            open={openLogoutModal}
            onClose={() => setOpenLogoutModal(false)}
          />
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
    </Box>
  );
}

export default connector(MenuWrapper);
