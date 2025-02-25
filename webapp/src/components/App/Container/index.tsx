/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { NavLink } from "react-router-dom";
import TravelExploreOutlinedIcon from "@mui/icons-material/TravelExploreOutlined";
import StorageIcon from "@mui/icons-material/Storage";
import CenterFocusStrongIcon from "@mui/icons-material/CenterFocusStrong";
import ClassOutlinedIcon from "@mui/icons-material/ClassOutlined";
import ApiIcon from "@mui/icons-material/Api";
import LogoutIcon from "@mui/icons-material/Logout";
import SettingsOutlinedIcon from "@mui/icons-material/SettingsOutlined";
import { Box, Divider, List, Toolbar, Tooltip, Typography, useTheme } from "@mui/material";
import { useMount } from "react-use";
import { setMenuOpen } from "@/redux/ducks/ui";
import { StyledDrawer } from "./styles";
import { getCurrentStudyId, isWebSocketConnected, isMenuOpen } from "@/redux/selectors";
import ConfirmationDialog from "../../common/dialogs/ConfirmationDialog";
import { logout } from "../../../redux/ducks/auth";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import { fetchUsers } from "../../../redux/ducks/users";
import { fetchGroups } from "../../../redux/ducks/groups";
import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import MenuItem from "./MenuItem";
import TaskIcon from "./TaskIcon";
import Logo from "@/components/common/Logo";
import { getConfig } from "@/services/config";

const topMenuItems = [
  {
    titleKey: "studies.title",
    link: "/studies",
    icon: <TravelExploreOutlinedIcon />,
  },
  { titleKey: "tasks.title", link: "/tasks", icon: <TaskIcon /> },
  { titleKey: "data.title", link: "/data", icon: <StorageIcon /> },
];

const subMenuItems = [
  {
    titleKey: "api.title",
    link: "/apidoc",
    icon: <ApiIcon />,
  },
  {
    titleKey: "documentation.title",
    link: "https://antares-doc.readthedocs.io",
    icon: <ClassOutlinedIcon />,
  },
];

const bottomMenuItems = [
  { titleKey: "settings.title", link: "/settings", icon: <SettingsOutlinedIcon /> },
];

interface Props {
  children: React.ReactNode;
}

function Container({ children }: Props) {
  const theme = useTheme();
  const { t } = useTranslation();
  const [openLogoutDialog, setOpenLogoutDialog] = useState(false);
  const isDrawerOpen = useAppSelector(isMenuOpen);
  const currentStudyId = useAppSelector(getCurrentStudyId);
  const isWsConnected = useAppSelector(isWebSocketConnected);
  const dispatch = useAppDispatch();

  const { version } = getConfig().versionInfo;

  useMount(() => {
    dispatch(fetchUsers());
    dispatch(fetchGroups());
  });

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Box sx={{ height: 1, display: "flex" }}>
        <StyledDrawer variant="permanent" open={isDrawerOpen}>
          <Toolbar disableGutters sx={[{ px: 2 }]}>
            <Tooltip title={version}>
              <NavLink
                to="/"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: theme.spacing(2),
                  textDecoration: "none",
                }}
              >
                <Logo pulse={!isWsConnected} />
                <Typography
                  sx={[
                    {
                      color: "secondary.main",
                      fontWeight: "bold",
                      opacity: isDrawerOpen ? 1 : 0,
                    },
                    (theme) => theme.applyStyles("light", { color: "primary.main" }),
                  ]}
                >
                  Antares Web
                </Typography>
              </NavLink>
            </Tooltip>
          </Toolbar>
          <Divider />
          <List sx={{ flex: 1 }}>
            {currentStudyId && (
              <MenuItem
                title={t("recentStudy.title")}
                icon={<CenterFocusStrongIcon />}
                isMenuOpen={isDrawerOpen}
                link={`/studies/${currentStudyId}`}
              />
            )}
            {topMenuItems.map(({ titleKey, icon, link }) => (
              <MenuItem
                key={titleKey}
                title={t(titleKey)}
                icon={icon}
                isMenuOpen={isDrawerOpen}
                link={link}
              />
            ))}
          </List>
          <List>
            {subMenuItems.map(({ titleKey, icon, link }) => (
              <MenuItem
                key={titleKey}
                title={t(titleKey)}
                icon={icon}
                isMenuOpen={isDrawerOpen}
                link={link}
              />
            ))}
          </List>
          <Divider />
          <List>
            {bottomMenuItems.map(({ titleKey, icon, link }) => (
              <MenuItem
                key={titleKey}
                title={t(titleKey)}
                icon={icon}
                isMenuOpen={isDrawerOpen}
                link={link}
              />
            ))}
            <MenuItem
              title={t("global.signOut")}
              icon={<LogoutIcon />}
              isMenuOpen={isDrawerOpen}
              onClick={() => setOpenLogoutDialog(true)}
            />
          </List>
          <Divider />
          <List>
            <MenuItem
              title={t("global.reduce")}
              icon={isDrawerOpen ? <ChevronLeftIcon /> : <ChevronRightIcon />}
              isMenuOpen={isDrawerOpen}
              onClick={() => dispatch(setMenuOpen(!isDrawerOpen))}
            />
          </List>
        </StyledDrawer>
        {children}
      </Box>
      {openLogoutDialog && (
        <ConfirmationDialog
          title={t("global.signOut")}
          titleIcon={LogoutIcon}
          onCancel={() => setOpenLogoutDialog(false)}
          onConfirm={() => dispatch(logout())}
          alert="warning"
          open
        >
          <Typography sx={{ px: 3, py: 1 }}>{t("dialog.message.signOut")}</Typography>
        </ConfirmationDialog>
      )}
    </>
  );
}

export default Container;
