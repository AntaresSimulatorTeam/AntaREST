import React, { useCallback, useEffect, useState, useRef, UIEvent } from 'react';
import { createStyles, makeStyles, Theme, Button, Paper, Typography } from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import Modal from '@material-ui/core/Modal';
import Backdrop from '@material-ui/core/Backdrop';
import Fade from '@material-ui/core/Fade';
import { CSSProperties } from '@material-ui/core/styles/withStyles';
import { connect, ConnectedProps } from 'react-redux';
import { exportText } from '../../services/utils/index';
import { addListener, removeListener } from '../../ducks/websockets';
import { WSEvent, WSLogMessage, WSMessage } from '../../common/types';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      overflowY: 'auto',
    },
    main: {
      backgroundColor: 'white',
      width: '80%',
      height: '80%',
      display: 'flex',
      flexFlow: 'column nowrap',
      alignItems: 'center',
    },
    titlebox: {
      height: '40px',
      width: '100%',
      display: 'flex',
      flexFlow: 'row nowrap',
      alignItems: 'center',
      backgroundColor: theme.palette.primary.main,
    },
    title: {
      fontWeight: 'bold',
      color: 'white',
      marginLeft: theme.spacing(2),
      overflow: 'hidden',
    },
    contentWrapper: {
      flex: '1',
      width: '100%',
      overflow: 'auto',
    },
    content: {
      padding: theme.spacing(3),
    },
    code: {
      whiteSpace: 'pre',
    },
    footer: {
      height: '60px',
      width: '100%',
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'center',
      alignItems: 'center',
      overflow: 'hidden',
      position: 'relative',
    },
    button: {
      margin: theme.spacing(2),
    },
    wrapTextIcon: {
      width: '24px',
      height: 'auto',
      cursor: 'pointer',
      color: theme.palette.primary.main,
      margin: theme.spacing(0, 3),
      '&:hover': {
        color: theme.palette.secondary.main,
      },
      position: 'absolute',
      right: theme.spacing(1),
    },
    downloadIcon: {
      color: 'white',
      cursor: 'pointer',
      margin: theme.spacing(0, 3),
      '&:hover': {
        color: theme.palette.secondary.main,
      },
    },
  }));

interface OwnTypes {
  isOpen: boolean;
  title: string;
  jobId?: string;
  content?: string;
  close: () => void;
  // eslint-disable-next-line react/require-default-props
  style?: CSSProperties;
}

const mapState = () => ({
});

const mapDispatch = ({
  addWsListener: addListener,
  removeWsListener: removeListener,
});

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps & OwnTypes;

let myFakeContent = 'Fake content ';
let index = 0;

const LogModal = (props: PropTypes) => {
  const { title, style, jobId, isOpen, content, close, addWsListener, removeWsListener } = props;
  const [logDetail, setLogDetail] = useState(content);
  const divRef = useRef<HTMLDivElement | null>(null);
  const logRef = useRef<HTMLDivElement | null>(null);
  const [autoscroll, setAutoScroll] = useState<boolean>(true);
  const classes = useStyles();
  const [t] = useTranslation();

  const updateLog = useCallback((ev: WSMessage) => {
    if (ev.type === WSEvent.STUDY_JOB_LOG_UPDATE) {
      const logEvent = ev.payload as WSLogMessage;
      if (logEvent.job_id === jobId) {
        setLogDetail((logDetail || '') + logEvent.log);
      }
    }
  }, [jobId, logDetail]);

  const handleGlobalKeyDown = (keyboardEvent: React.KeyboardEvent<HTMLDivElement>) => {
    if (keyboardEvent.key === 'a' && keyboardEvent.ctrlKey) {
      if (divRef.current) {
        const range = document.createRange();
        range.selectNode(divRef.current);
        const selection = window.getSelection();
        if (selection !== null) {
          selection.addRange(range);
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
      exportText(logDetail, 'log_detail.txt');
    }
  };

  useEffect(() => {
    setTimeout(() => {
      myFakeContent += `Fake Content. ${index} \n`;
      index += 1;
      setLogDetail(myFakeContent);
    }, 1000);
  }, [logDetail]);

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
    addWsListener(updateLog);
    return () => removeWsListener(updateLog);
  }, [updateLog, addWsListener, removeWsListener]);

  return (
    <Modal
      aria-labelledby="transition-modal-title"
      aria-describedby="transition-modal-description"
      className={classes.root}
      open={isOpen}
      closeAfterTransition
      BackdropComponent={Backdrop}
      BackdropProps={{
        timeout: 500,
      }}
    >
      <Fade in={isOpen}>
        <Paper onKeyDown={handleGlobalKeyDown} className={classes.main} style={style !== undefined ? style : {}}>
          <div className={classes.titlebox}>
            <Typography className={classes.title}>{title}</Typography>
            <FontAwesomeIcon className={classes.downloadIcon} icon="download" onClick={onDownload} />
          </div>
          <div className={classes.contentWrapper} ref={logRef} onScroll={onScroll}>
            <div className={classes.content} id="log-content" ref={divRef}>
              <code className={classes.code}>{logDetail}</code>
            </div>
          </div>
          <div className={classes.footer}>
            <Button variant="contained" className={classes.button} onClick={close}>
              {t('main:closeButton')}
            </Button>
          </div>
        </Paper>
      </Fade>
    </Modal>
  );
};

LogModal.defaultProps = {
  content: undefined,
  jobId: undefined,
};

export default connector(LogModal);
