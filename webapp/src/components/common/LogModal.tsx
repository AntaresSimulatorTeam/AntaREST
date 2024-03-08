import {
  useCallback,
  useEffect,
  useState,
  useRef,
  UIEvent,
  KeyboardEvent,
  CSSProperties,
} from "react";
import { Box, Button, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import DownloadIcon from "@mui/icons-material/Download";
import { exportText } from "../../services/utils/index";
import { WSEvent, WSLogMessage, WSMessage } from "../../common/types";
import SimpleLoader from "./loaders/SimpleLoader";
import BasicDialog from "./dialogs/BasicDialog";
import {
  addWsMessageListener,
  sendWsSubscribeMessage,
  WsChannel,
} from "../../services/webSockets";

interface Props {
  isOpen: boolean;
  jobId?: string;
  followLogs?: boolean;
  content?: string;
  close: VoidFunction;
  style?: CSSProperties;
  loading?: boolean;
}

function LogModal(props: Props) {
  const { style, jobId, followLogs, loading, isOpen, content, close } = props;
  const [logDetail, setLogDetail] = useState(content);
  const divRef = useRef<HTMLDivElement | null>(null);
  const logRef = useRef<HTMLDivElement | null>(null);
  const [autoScroll, setAutoScroll] = useState<boolean>(true);
  const [t] = useTranslation();

  const updateLog = useCallback(
    (ev: WSMessage<WSLogMessage>) => {
      if (ev.type === WSEvent.STUDY_JOB_LOG_UPDATE) {
        const logEvent = ev.payload;
        if (logEvent.job_id === jobId) {
          setLogDetail((logDetail || "") + logEvent.log);
        }
      }
    },
    [jobId, logDetail],
  );

  const handleGlobalKeyDown = (
    keyboardEvent: KeyboardEvent<HTMLDivElement>,
  ) => {
    if (keyboardEvent.key === "a" && keyboardEvent.ctrlKey) {
      if (divRef.current) {
        const selection = window.getSelection();
        if (selection !== null) {
          selection.selectAllChildren(divRef.current);
        }
      }
      keyboardEvent.preventDefault();
    }
  };

  const scrollToEnd = () => {
    if (logRef.current) {
      const myDiv = logRef.current.scrollHeight;
      logRef.current.scrollTo(0, myDiv - 10);
    }
  };

  const onDownload = () => {
    if (logDetail !== undefined) {
      exportText(logDetail, "log_detail.txt");
    }
  };

  const onScroll = (ev: UIEvent<HTMLDivElement>) => {
    const element = ev.target as HTMLDivElement;
    if (element.scrollHeight - element.scrollTop <= element.clientHeight + 20) {
      setAutoScroll(true);
    } else {
      setAutoScroll(false);
    }
  };

  useEffect(() => {
    setLogDetail(content);
  }, [content]);

  useEffect(() => {
    if (logRef.current) {
      if (autoScroll) {
        scrollToEnd();
      }
    }
  }, [logDetail, autoScroll]);

  useEffect(() => {
    if (followLogs) {
      if (jobId) {
        const removeSubscription = sendWsSubscribeMessage(
          WsChannel.JobLogs + jobId,
        );
        const removeMessageListener = addWsMessageListener(updateLog);
        return () => {
          removeSubscription();
          removeMessageListener();
        };
      }
    }
  }, [followLogs, jobId, updateLog]);

  return (
    <BasicDialog
      open={isOpen}
      onClose={close}
      title={
        <Box
          width="100%"
          height="64px"
          display="flex"
          flexDirection="row"
          justifyContent="flex-start"
          alignItems="center"
          py={2}
          px={3}
          boxSizing="border-box"
        >
          <Typography
            sx={{
              color: "white",
              fontWeight: 500,
              fontSize: "20px",
              boxSizing: "border-box",
            }}
          >
            {t("global.logs")}
          </Typography>
          <DownloadIcon
            sx={{
              color: "white",
              cursor: "pointer",
              mx: 3,
              "&:hover": {
                color: "secondary.main",
              },
            }}
            onClick={onDownload}
          />
        </Box>
      }
      contentProps={{
        sx: { p: 0, height: "60vh", overflow: "hidden" },
      }}
      fullWidth
      maxWidth="lg"
      actions={
        <Button variant="text" color="primary" onClick={close}>
          {t("button.close")}
        </Button>
      }
    >
      <Box
        onKeyDown={handleGlobalKeyDown}
        sx={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexFlow: "column nowrap",
          alignItems: "center",
          zIndex: 1,
          ...style,
        }}
      >
        <Box
          width="100%"
          overflow="auto"
          position="relative"
          flex={1}
          ref={logRef}
          onScroll={onScroll}
        >
          {loading ? (
            <SimpleLoader />
          ) : (
            <Box sx={{ p: 3 }} id="log-content" ref={divRef}>
              <code style={{ whiteSpace: "pre" }}>{logDetail}</code>
            </Box>
          )}
        </Box>
      </Box>
    </BasicDialog>
  );
}

LogModal.defaultProps = {
  content: undefined,
  jobId: undefined,
  followLogs: false,
  loading: false,
  style: {},
};

export default LogModal;
