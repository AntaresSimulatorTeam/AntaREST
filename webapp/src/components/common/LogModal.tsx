import {
  useCallback,
  useEffect,
  useState,
  useRef,
  UIEvent,
  KeyboardEvent,
  CSSProperties,
} from "react";
import { Box, Button, Paper, Typography, Modal, Backdrop } from "@mui/material";
import { useTranslation } from "react-i18next";
import DownloadIcon from "@mui/icons-material/Download";
import { connect, ConnectedProps } from "react-redux";
import { exportText } from "../../services/utils/index";
import { addListener, removeListener } from "../../store/websockets";
import { WSEvent, WSLogMessage, WSMessage } from "../../common/types";
import SimpleLoader from "./loaders/SimpleLoader";
import { scrollbarStyle } from "../../theme";

interface OwnTypes {
  isOpen: boolean;
  title: string;
  jobId?: string;
  followLogs?: boolean;
  content?: string;
  close: () => void;
  style?: CSSProperties;
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
    title,
    style,
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
  const divRef = useRef<HTMLDivElement | null>(null);
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
    <Modal
      aria-labelledby="transition-modal-title"
      aria-describedby="transition-modal-description"
      open={isOpen}
      closeAfterTransition
      BackdropComponent={Backdrop}
      BackdropProps={{
        timeout: 500,
      }}
      sx={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        boxSizing: "border-box",
        overflowY: "auto",
      }}
    >
      <Paper
        onKeyDown={handleGlobalKeyDown}
        sx={{
          width: "80%",
          height: "80%",
          display: "flex",
          flexFlow: "column nowrap",
          alignItems: "center",
          zIndex: 1,
          ...style,
        }}
      >
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
            {title}
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
        <Box
          width="100%"
          overflow="auto"
          position="relative"
          flex={1}
          ref={logRef}
          onScroll={onScroll}
          sx={scrollbarStyle}
        >
          {loading ? (
            <SimpleLoader />
          ) : (
            <Box sx={{ p: 3 }} id="log-content" ref={divRef}>
              <code style={{ whiteSpace: "pre" }}>{logDetail}</code>
            </Box>
          )}
        </Box>
        <Box
          height="60px"
          width="100%"
          display="flex"
          justifyContent="center"
          alignItems="center"
          overflow="hidden"
          position="relative"
        >
          <Button variant="contained" sx={{ m: 2 }} onClick={close}>
            {t("main:closeButton")}
          </Button>
        </Box>
      </Paper>
    </Modal>
  );
}

LogModal.defaultProps = {
  content: undefined,
  jobId: undefined,
  followLogs: false,
  loading: false,
  style: {},
};

export default connector(LogModal);
