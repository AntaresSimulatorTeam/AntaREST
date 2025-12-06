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

import ConfirmationDialog from "@/components/dialogs/ConfirmationDialog";
import Logo from "@/components/Logo";
import { useAppMode } from "@/hooks/useAppMode";
import { logout } from "@/redux/ducks/auth";
import { fetchGroups } from "@/redux/ducks/groups";
import { fetchStudies } from "@/redux/ducks/studies";
import { setFormCloseDialogStatus, setMenuOpen } from "@/redux/ducks/ui";
import { fetchUsers } from "@/redux/ducks/users";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import {
  getCurrentStudyId,
  getFormState,
  isMenuOpen,
  isWebSocketConnected,
} from "@/redux/selectors";
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
import { Box, Divider, List, Toolbar, Tooltip, Typography, useTheme } from "@mui/material";
import { Link } from "@tanstack/react-router";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useMount } from "react-use";
import FavoritesMenu from "./FavoritesMenu";
import SidebarItem from "./SidebarItem";
import { StyledDrawer } from "./styles";
import TaskIcon from "./TaskIcon";

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
  const formState = useAppSelector(getFormState);
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
              <Link
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
              </Link>
            </Tooltip>
          </Toolbar>
          <Divider />
          <List sx={{ flex: 1 }}>
            {currentStudyId && (
              <SidebarItem
                title={t("recentStudy.title")}
                icon={<CenterFocusStrongIcon />}
                link={`/studies/${currentStudyId}`}
              />
            )}
            <FavoritesMenu />
            {topMenuItems.map(({ titleKey, icon, link }) => (
              <SidebarItem key={titleKey} title={t(titleKey)} icon={icon} link={link} />
            ))}
          </List>
          <List>
            {subMenuItems.map(({ titleKey, icon, link }) => (
              <SidebarItem key={titleKey} title={t(titleKey)} icon={icon} link={link} />
            ))}
          </List>
          <Divider />
          <List>
            {bottomMenuItems.map(({ titleKey, icon, link }) => (
              <SidebarItem key={titleKey} title={t(titleKey)} icon={icon} link={link} />
            ))}
            {isWebMode && (
              <SidebarItem
                title={t("global.signOut")}
                icon={<LogoutIcon />}
                onClick={() => setOpenLogoutDialog(true)}
              />
            )}
          </List>
          <Divider />
          <List>
            <SidebarItem
              title={t("global.reduce")}
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
      {formState.closeDialogStatus === "opened" && (
        <ConfirmationDialog
          open
          alert="warning"
          onConfirm={() => dispatch(setFormCloseDialogStatus("confirmed"))}
          onCancel={() => dispatch(setFormCloseDialogStatus("canceled"))}
        >
          {formState.status.isSubmitting ? t("form.submit.inProgress") : t("form.changeNotSaved")}
        </ConfirmationDialog>
      )}
    </>
  );
}

export default Container;
