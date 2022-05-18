import { PropsWithChildren, useCallback, useEffect, useRef } from "react";
import debug from "debug";
import { connect, ConnectedProps } from "react-redux";
import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useLocation } from "react-router-dom";
import CircleIcon from "@mui/icons-material/Circle";
import { useSnackbar, VariantType } from "notistack";
import { red } from "@mui/material/colors";
import { TaskEventPayload, WSEvent, WSMessage } from "../../common/types";
import { getTask } from "../../services/api/tasks";
import { AppState } from "../../redux/ducks";
import { addMessageListener } from "../../services/webSockets";
import {
  incrementTaskNotifications,
  resetTaskNotifications,
} from "../../redux/ducks/ui";

const logError = debug("antares:downloadbadge:error");

const mapState = (state: AppState) => ({
  notificationCount: state.ui.taskNotificationsCount,
});

const mapDispatch = {
  addTasksNotification: incrementTaskNotifications,
  clearTasksNotification: resetTaskNotifications,
};

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = PropsWithChildren<ReduxProps>;

function NotificationBadge(props: PropTypes) {
  const {
    children,
    notificationCount,
    addTasksNotification,
    clearTasksNotification,
  } = props;
  const [t] = useTranslation();
  const location = useLocation();
  const { enqueueSnackbar } = useSnackbar();
  const ref = useRef<HTMLDivElement>(null);

  const newNotification = useCallback(
    (message: string, variantType?: VariantType) => {
      if (location.pathname !== "/tasks") {
        addTasksNotification();
      }
      enqueueSnackbar(t(message), { variant: variantType || "info" });
    },
    [addTasksNotification, enqueueSnackbar, location.pathname, t]
  );

  useEffect(() => {
    const listener = async (ev: WSMessage) => {
      if (ev.type === WSEvent.DOWNLOAD_CREATED) {
        newNotification("downloads:newDownload");
      } else if (ev.type === WSEvent.DOWNLOAD_READY) {
        newNotification("downloads:downloadReady");
      } else if (ev.type === WSEvent.DOWNLOAD_FAILED) {
        newNotification("singlestudy:failedToExportOutput", "error");
      } else if (ev.type === WSEvent.TASK_ADDED) {
        const taskId = (ev.payload as TaskEventPayload).id;
        try {
          const task = await getTask(taskId);
          if (task.type === "COPY") {
            newNotification("studymanager:studycopying");
          } else if (task.type === "ARCHIVE") {
            newNotification("studymanager:studyarchiving");
          } else if (task.type === "UNARCHIVE") {
            newNotification("studymanager:studyunarchiving");
          } else if (task.type === "SCAN") {
            newNotification("studymanager:scanFolderSuccess");
          }
        } catch (error) {
          logError(error);
        }
      }
    };

    return addMessageListener(listener);
  }, [newNotification]);

  useEffect(() => {
    if (location.pathname === "/tasks") {
      clearTasksNotification();
    }
  }, [location, clearTasksNotification]);

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

export default connector(NotificationBadge);
