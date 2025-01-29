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

import { useCallback, useEffect, useRef } from "react";
import debug from "debug";
import { Box, Typography, colors } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useLocation } from "react-router-dom";
import CircleIcon from "@mui/icons-material/Circle";
import { useSnackbar, type VariantType } from "notistack";
import { getTask } from "../../../services/api/tasks";
import { addWsEventListener } from "../../../services/webSocket/ws";
import { incrementTaskNotifications, resetTaskNotifications } from "../../../redux/ducks/ui";
import { getTaskNotificationsCount } from "../../../redux/selectors";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import { TaskType } from "../../../services/api/tasks/constants";
import { WsEventType } from "@/services/webSocket/constants";
import type { WsEvent } from "@/services/webSocket/types";

const logError = debug("antares:downloadbadge:error");

interface Props {
  children: React.ReactNode;
}

function NotificationBadge(props: Props) {
  const { children } = props;
  const [t] = useTranslation();
  const location = useLocation();
  const { enqueueSnackbar } = useSnackbar();
  const ref = useRef<HTMLDivElement>(null);
  const notificationCount = useAppSelector(getTaskNotificationsCount);
  const dispatch = useAppDispatch();

  const newNotification = useCallback(
    (message?: string, variantType?: VariantType) => {
      if (location.pathname !== "/tasks") {
        dispatch(incrementTaskNotifications());
      }
      if (message) {
        enqueueSnackbar(t(message), { variant: variantType || "info" });
      }
    },
    [dispatch, enqueueSnackbar, location.pathname, t],
  );

  useEffect(() => {
    const listener = async (ev: WsEvent) => {
      if (ev.type === WsEventType.DownloadCreated) {
        newNotification("downloads.newDownload");
      } else if (ev.type === WsEventType.DownloadReady) {
        newNotification("downloads.downloadReady");
      } else if (ev.type === WsEventType.DownloadFailed) {
        newNotification("study.error.exportOutput", "error");
      } else if (ev.type === WsEventType.TaskAdded) {
        try {
          const task = await getTask({ id: ev.payload.id });
          if (task.type === TaskType.Copy) {
            newNotification("studies.studycopying");
          } else if (task.type === TaskType.Archive) {
            newNotification("studies.studyarchiving");
          } else if (task.type === TaskType.Unarchive) {
            newNotification("studies.studyunarchiving");
          } else if (task.type === TaskType.Scan) {
            newNotification("studies.success.scanFolder");
          } else if (
            task.type === TaskType.UpgradeStudy ||
            task.type === TaskType.ThermalClusterSeriesGeneration
          ) {
            newNotification();
          }
        } catch (error) {
          logError(error);
        }
      }
    };

    return addWsEventListener(listener);
  }, [newNotification]);

  useEffect(() => {
    if (location.pathname === "/tasks") {
      dispatch(resetTaskNotifications());
    }
  }, [dispatch, location.pathname]);

  return (
    <Box position="relative">
      <Box ref={ref}>{children}</Box>
      {ref.current && notificationCount > 0 && (
        <Box
          sx={{
            position: "absolute",
            right: "10px",
            bottom: "-10px",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <Typography
            sx={{
              fontSize: "12px",
              color: "white",
              position: "absolute",
            }}
          >
            {notificationCount}
          </Typography>
          <CircleIcon sx={{ fontSize: "20px", color: colors.red[800] }} />
        </Box>
      )}
    </Box>
  );
}

export default NotificationBadge;
