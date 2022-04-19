import { PropsWithChildren, useEffect, useRef, useState } from "react";
import debug from "debug";
import { connect, ConnectedProps } from "react-redux";
import { Popover, Box, Paper } from "@mui/material";
import { useTranslation } from "react-i18next";
import { addListener, removeListener } from "../../store/websockets";
import { TaskEventPayload, WSEvent, WSMessage } from "../../common/types";
import { getTask } from "../../services/api/tasks";

const logError = debug("antares:downloadbadge:error");

const mapState = () => ({});

const mapDispatch = {
  addWsListener: addListener,
  removeWsListener: removeListener,
};

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = PropsWithChildren<ReduxProps>;

function DownloadBadge(props: PropTypes) {
  const { addWsListener, removeWsListener, children } = props;
  const [t] = useTranslation();
  const ref = useRef<HTMLDivElement>(null);
  const [notificationMessage, setNotificationMessage] = useState<string>();

  useEffect(() => {
    const listener = async (ev: WSMessage) => {
      if (ev.type === WSEvent.DOWNLOAD_CREATED) {
        setNotificationMessage("downloads:newDownload");
      } else if (ev.type === WSEvent.DOWNLOAD_READY) {
        setNotificationMessage("downloads:downloadReady");
      } else if (ev.type === WSEvent.TASK_ADDED) {
        const taskId = (ev.payload as TaskEventPayload).id;
        try {
          const task = await getTask(taskId);
          if (task.type === "COPY") {
            setNotificationMessage("studymanager:studycopying");
          } else if (task.type === "ARCHIVE") {
            setNotificationMessage("studymanager:studyarchiving");
          } else if (task.type === "UNARCHIVE") {
            setNotificationMessage("studymanager:studyunarchiving");
          } else if (task.type === "SCAN") {
            setNotificationMessage("studymanager:scanFolderSuccess");
          }
        } catch (error) {
          logError(error);
        }
      }
    };
    addWsListener(listener);
    return () => removeWsListener(listener);
  }, [addWsListener, removeWsListener]);

  useEffect(() => {
    if (notificationMessage) {
      setTimeout(() => {
        setNotificationMessage(undefined);
      }, 4000);
    }
  }, [notificationMessage]);

  return (
    <>
      <Box ref={ref}>{children}</Box>
      {ref.current && (
        <Popover
          id="download-badge-content"
          open={!!notificationMessage}
          anchorEl={ref.current}
          onClose={() => setNotificationMessage(undefined)}
          anchorOrigin={{
            vertical: "center",
            horizontal: "right",
          }}
          transformOrigin={{
            vertical: "center",
            horizontal: "left",
          }}
          PaperProps={{
            style: {
              background: "transparent",
              marginLeft: "8px",
            },
          }}
        >
          <Box
            display="flex"
            flexDirection="row"
            alignItems="center"
            justifyContent="center"
            width="300px"
            height="100px"
          >
            <Paper
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: "300px",
                height: "100px",
              }}
            >
              <Box color="white">{t(notificationMessage || "")}</Box>
            </Paper>
          </Box>
        </Popover>
      )}
    </>
  );
}

export default connector(DownloadBadge);
