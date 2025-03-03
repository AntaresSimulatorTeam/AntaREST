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

import { useTranslation } from "react-i18next";
import { Box, Button, Typography, useTheme } from "@mui/material";
import { useLocation, useNavigate } from "react-router-dom";
import ErrorIcon from "@mui/icons-material/Error";
import { isUserAdmin } from "../../../services/utils";
import MessageInfoDialog from "./MessageInfoDialog";
import { setMaintenanceMode } from "../../../redux/ducks/ui";
import { getAuthUser, getMaintenanceMode } from "../../../redux/selectors";
import * as api from "../../../services/api/maintenance";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import { useMount } from "react-use";

interface Props {
  children: React.ReactNode;
}

function MaintenanceMode({ children }: Props) {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
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

  const handleLoginClick = () => {
    navigate("/login");
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (
    maintenanceMode &&
    (user === undefined || !isUserAdmin(user)) &&
    location.pathname !== "/login"
  ) {
    return (
      <>
        <Button
          variant="contained"
          sx={{
            position: "absolute",
            top: theme.spacing(2),
            right: theme.spacing(2),
          }}
          onClick={handleLoginClick}
        >
          {t("global.signIn")}
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
