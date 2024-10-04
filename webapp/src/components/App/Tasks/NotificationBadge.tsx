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

import { ReactNode, useCallback, useEffect, useRef } from "react";
import debug from "debug";
import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useLocation } from "react-router-dom";
import CircleIcon from "@mui/icons-material/Circle";
import { useSnackbar, VariantType } from "notistack";
import { red } from "@mui/material/colors";
import { TaskEventPayload, WSEvent, WSMessage } from "../../../common/types";
import { getTask } from "../../../services/api/tasks";
import { addWsMessageListener } from "../../../services/webSockets";
import {
  incrementTaskNotifications,
  resetTaskNotifications,
} from "../../../redux/ducks/ui";
import { getTaskNotificationsCount } from "../../../redux/selectors";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import useAppSelector from "../../../redux/hooks/useAppSelector";

const logError = debug("antares:downloadbadge:error");

interface Props {
  children: ReactNode;
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
    (message: string, variantType?: VariantType) => {
      if (location.pathname !== "/tasks") {
        dispatch(incrementTaskNotifications());
      }
      enqueueSnackbar(t(message), { variant: variantType || "info" });
    },
    [dispatch, enqueueSnackbar, location.pathname, t],
  );

  useEffect(() => {
    const listener = async (ev: WSMessage<TaskEventPayload>) => {
      if (ev.type === WSEvent.DOWNLOAD_CREATED) {
        newNotification("downloads.newDownload");
      } else if (ev.type === WSEvent.DOWNLOAD_READY) {
        newNotification("downloads.downloadReady");
      } else if (ev.type === WSEvent.DOWNLOAD_FAILED) {
        newNotification("study.error.exportOutput", "error");
      } else if (ev.type === WSEvent.TASK_ADDED) {
        try {
          const task = await getTask(ev.payload.id);
          if (task.type === "COPY") {
            newNotification("studies.studycopying");
          } else if (task.type === "ARCHIVE") {
            newNotification("studies.studyarchiving");
          } else if (task.type === "UNARCHIVE") {
            newNotification("studies.studyunarchiving");
          } else if (task.type === "SCAN") {
            newNotification("studies.success.scanFolder");
          } else if (task.type === "UPGRADE_STUDY") {
            newNotification("study.message.upgradeInProgress");
          } else if (task.type === "THERMAL_CLUSTER_SERIES_GENERATION") {
            newNotification("tasks.thermalClusterSeriesGeneration");
          }
        } catch (error) {
          logError(error);
        }
      }
    };

    return addWsMessageListener(listener);
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
          <CircleIcon sx={{ fontSize: "20px", color: red[800] }} />
        </Box>
      )}
    </Box>
  );
}

export default NotificationBadge;
