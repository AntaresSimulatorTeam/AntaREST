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

import { logout } from "@/redux/ducks/auth";
import { setMaintenanceMode } from "@/redux/ducks/ui";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getAuthUser, getMaintenanceMode } from "@/redux/selectors";
import * as api from "@/services/api/maintenance";
import { isUserAdmin } from "@/services/utils";
import ErrorIcon from "@mui/icons-material/Error";
import LogoutIcon from "@mui/icons-material/Logout";
import { Box, Button, Typography, useTheme } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useMount } from "react-use";
import MessageInfoDialog from "./MessageInfoDialog";

interface Props {
  children: React.ReactNode;
}

function MaintenanceMode({ children }: Props) {
  const { t } = useTranslation();
  const user = useAppSelector(getAuthUser);
  const maintenanceMode = useAppSelector(getMaintenanceMode);
  const dispatch = useAppDispatch();
  const theme = useTheme();

  useMount(async () => {
    const tmpMaintenance = await api.getMaintenanceMode();
    dispatch(setMaintenanceMode(tmpMaintenance));
  });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleLogoutClick = () => {
    dispatch(logout());
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (maintenanceMode && (user === undefined || !isUserAdmin(user))) {
    return (
      <>
        <Button
          variant="contained"
          sx={{
            position: "absolute",
            top: theme.spacing(2),
            right: theme.spacing(2),
          }}
          onClick={handleLogoutClick}
          color="secondary"
          startIcon={<LogoutIcon />}
        >
          {t("global.signOut")}
        </Button>
        <Box
          sx={{
            height: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 2,
          }}
        >
          <ErrorIcon sx={{ fontSize: 80 }} />
          <Typography variant="h4" sx={{ whiteSpace: "pre-wrap" }}>
            {t("maintenance.message")}
          </Typography>
        </Box>
        <MessageInfoDialog />
      </>
    );
  }

  return (
    <>
      {children}
      <MessageInfoDialog />
    </>
  );
}

export default MaintenanceMode;
