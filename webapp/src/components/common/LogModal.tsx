import {
  useCallback,
  useEffect,
  useState,
  useRef,
  UIEvent,
  KeyboardEvent,
} from "react";
import { Box, Button, IconButton } from "@mui/material";
import { useTranslation } from "react-i18next";
import DownloadIcon from "@mui/icons-material/Download";
import { connect, ConnectedProps } from "react-redux";
import SummarizeIcon from "@mui/icons-material/Summarize";
import { exportText } from "../../services/utils/index";
import { addListener, removeListener } from "../../store/websockets";
import { WSEvent, WSLogMessage, WSMessage } from "../../common/types";
import SimpleLoader from "./loaders/SimpleLoader";
import BasicDialog from "./dialogs/BasicDialog";

interface OwnTypes {
  isOpen: boolean;
  jobId?: string;
  followLogs?: boolean;
  content?: string;
  close: () => void;
  loading?: boolean;
}

const mapState = () => ({});

const mapDispatch = {
  addWsListener: addListener,
  removeWsListener: removeListener,
};

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps & OwnTypes;

function LogModal(props: PropTypes) {
  const {
    jobId,
    followLogs,
    loading,
    isOpen,
    content,
    close,
    addWsListener,
    removeWsListener,
  } = props;
  const [logDetail, setLogDetail] = useState(content);
  const logRef = useRef<HTMLDivElement | null>(null);
  const [autoscroll, setAutoScroll] = useState<boolean>(true);
  const [t] = useTranslation();

  const updateLog = useCallback(
    (ev: WSMessage) => {
      if (ev.type === WSEvent.STUDY_JOB_LOG_UPDATE) {
        const logEvent = ev.payload as WSLogMessage;
        if (logEvent.job_id === jobId) {
          setLogDetail((logDetail || "") + logEvent.log);
        }
      }
    },
    [jobId, logDetail]
  );

  const handleGlobalKeyDown = (
    keyboardEvent: KeyboardEvent<HTMLDivElement>
  ) => {
    if (keyboardEvent.key === "a" && keyboardEvent.ctrlKey) {
      if (logRef.current) {
        const selection = window.getSelection();
        if (selection !== null) {
          selection.selectAllChildren(logRef.current);
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
      if (autoscroll) {
        scrollToEnd();
      }
    }
  }, [logDetail, autoscroll]);

  useEffect(() => {
    if (followLogs) {
      addWsListener(updateLog);
      return () => removeWsListener(updateLog);
    }
    return () => {
      /* noop */
    };
  }, [updateLog, followLogs, addWsListener, removeWsListener]);

  return (
    <BasicDialog
      open={isOpen}
      title={t("singlestudy:taskLog")}
      titleIcon={SummarizeIcon}
      actions={<Button onClick={close}>{t("main:closeButton")}</Button>}
      onKeyDown={handleGlobalKeyDown}
      onClose={close}
      fullWidth
    >
      <Box
        sx={{
          position: "relative",
          display: "flex",
          width: "100%",
          overflow: "hidden",
          pb: 4,
        }}
      >
        {loading ? (
          <SimpleLoader />
        ) : (
          <Box
            sx={{ overflow: "auto", width: "100%", flex: 1, p: 3 }}
            component="pre"
            ref={logRef}
            onScroll={onScroll}
          >
            {logDetail}
          </Box>
        )}
        <IconButton
          sx={{ position: "absolute", bottom: 3, right: 3 }}
          onClick={onDownload}
        >
          <DownloadIcon />
        </IconButton>
      </Box>
    </BasicDialog>
  );
}

LogModal.defaultProps = {
  content: undefined,
  jobId: undefined,
  followLogs: false,
  loading: false,
};

export default connector(LogModal);
