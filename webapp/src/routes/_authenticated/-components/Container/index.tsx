/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import ConfirmationDialog from "@/components/dialogs/ConfirmationDialog";
import Logo from "@/components/Logo";
import RouterLink from "@/components/router/RouterLink";
import { useAppMode } from "@/hooks/useAppMode";
import { logout } from "@/redux/ducks/auth";
import { fetchGroups } from "@/redux/ducks/groups";
import { fetchStudies } from "@/redux/ducks/studies";
import { setMenuOpen } from "@/redux/ducks/ui";
import { fetchUsers } from "@/redux/ducks/users";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getCurrentStudyId, isMenuOpen, isWebSocketConnected } from "@/redux/selectors";
import { getConfig } from "@/services/config";
import ApiIcon from "@mui/icons-material/Api";
import CenterFocusStrongIcon from "@mui/icons-material/CenterFocusStrong";
import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import ClassOutlinedIcon from "@mui/icons-material/ClassOutlined";
import LogoutIcon from "@mui/icons-material/Logout";
import SettingsOutlinedIcon from "@mui/icons-material/SettingsOutlined";
import StorageIcon from "@mui/icons-material/Storage";
import TravelExploreOutlinedIcon from "@mui/icons-material/TravelExploreOutlined";
import { Box, Divider, List, Toolbar, Tooltip, Typography } from "@mui/material";
import { linkOptions } from "@tanstack/react-router";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useMount } from "react-use";
import FavoritesMenu from "./FavoritesMenu";
import SidebarItem, { type SidebarItemProps } from "./SidebarItem";
import { StyledDrawer } from "./styles";
import TaskIcon from "./TaskIcon";

const topMenuItems: SidebarItemProps[] = [
  {
    label: (t) => t("studies.title"),
    linkOptions: linkOptions({ to: "/studies" }),
    icon: <TravelExploreOutlinedIcon />,
  },
  {
    label: (t) => t("tasks.title"),
    linkOptions: linkOptions({
      to: "/tasks",
    }),
    icon: <TaskIcon />,
  },
  {
    label: (t) => t("data.title"),
    linkOptions: linkOptions({
      to: "/data",
    }),
    icon: <StorageIcon />,
  },
];

const subMenuItems: SidebarItemProps[] = [
  {
    label: (t) => t("api.title"),
    linkOptions: linkOptions({
      to: "/apidoc",
    }),
    icon: <ApiIcon />,
  },
  {
    label: (t) => t("documentation.title"),
    linkOptions: {
      href: "https://antares-doc.readthedocs.io",
    },
    icon: <ClassOutlinedIcon />,
  },
];

const bottomMenuItems: SidebarItemProps[] = [
  {
    label: (t) => t("settings.title"),
    linkOptions: linkOptions({
      to: "/settings",
    }),
    icon: <SettingsOutlinedIcon />,
  },
];

interface Props {
  children: React.ReactNode;
}

function Container({ children }: Props) {
  const { t } = useTranslation();
  const [openLogoutDialog, setOpenLogoutDialog] = useState(false);
  const isDrawerOpen = useAppSelector(isMenuOpen);
  const currentStudyId = useAppSelector(getCurrentStudyId);
  const isWsConnected = useAppSelector(isWebSocketConnected);
  const dispatch = useAppDispatch();
  const { isWebMode } = useAppMode();

  const { version } = getConfig().versionInfo;

  useMount(() => {
    dispatch(fetchUsers());
    dispatch(fetchGroups());
    dispatch(fetchStudies());
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
              <RouterLink
                to="/"
                underline="none"
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 2,
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
              </RouterLink>
            </Tooltip>
          </Toolbar>
          <Divider />
          <List sx={{ flex: 1 }}>
            {currentStudyId && (
              <SidebarItem
                label={t("recentStudy.title")}
                icon={<CenterFocusStrongIcon />}
                linkOptions={{
                  to: "/studies/$studyId",
                  params: { studyId: currentStudyId },
                }}
                disableAutoActive
              />
            )}
            <FavoritesMenu />
            {topMenuItems.map((item, index) => (
              <SidebarItem key={index} {...item} />
            ))}
          </List>
          <List>
            {subMenuItems.map((item, index) => (
              <SidebarItem key={index} {...item} />
            ))}
          </List>
          <Divider />
          <List>
            {bottomMenuItems.map((item, index) => (
              <SidebarItem key={index} {...item} />
            ))}
            {isWebMode && (
              <SidebarItem
                label={t("global.signOut")}
                icon={<LogoutIcon />}
                onClick={() => setOpenLogoutDialog(true)}
              />
            )}
          </List>
          <Divider />
          <List>
            <SidebarItem
              label={t("global.reduce")}
              icon={isDrawerOpen ? <ChevronLeftIcon /> : <ChevronRightIcon />}
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
