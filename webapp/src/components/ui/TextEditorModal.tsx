import React, { useEffect, useState } from 'react';
import { createStyles, makeStyles, Theme, Button, Paper, Typography } from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import Modal from '@material-ui/core/Modal';
import Backdrop from '@material-ui/core/Backdrop';
import Fade from '@material-ui/core/Fade';
import { CSSProperties } from '@material-ui/core/styles/withStyles';
import { Editor, EditorState, RichUtils } from 'draft-js';
import FormatAlignCenterIcon from '@material-ui/icons/FormatAlignCenter';
import FormatAlignLeftIcon from '@material-ui/icons/FormatAlignLeft';
import FormatAlignRightIcon from '@material-ui/icons/FormatAlignRight';
import { defaultBlockRenderMap, DraftJsToHtml, htmlToDraftJs } from './Utils';

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
      overflow: 'hidden',
    },
    content: {
      padding: theme.spacing(3),
      height: 'calc(100% - 40px)',
      width: '100%',
      boxSizing: 'border-box',
      overflow: 'auto',
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
    },
    button: {
      margin: theme.spacing(2),
    },
    header: {
      display: 'flex',
      width: '100%',
      height: '40px',
      padding: theme.spacing(0, 3),
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      backgroundColor: 'white',
    },
    textIcon: {
      margin: theme.spacing(0, 2),
      fontSize: '1em',
      color: theme.palette.primary.main,
      cursor: 'pointer',
      '&:hover': {
        color: theme.palette.secondary.main,
      },
    },
    alignIcon: {
      width: '20px',
      height: 'auto',
      color: theme.palette.primary.main,
      cursor: 'pointer',
      margin: theme.spacing(0, 2),
      '&:hover': {
        color: theme.palette.secondary.main,
      },
    },
  }));

interface PropTypes {
  isOpen: boolean;
  title: string;
  content?: string;
  close: () => void;
  // eslint-disable-next-line react/require-default-props
  onSave: (content: string) => void;
  style?: CSSProperties;
}

const TextEditorModal = (props: PropTypes) => {
  const { title, style, isOpen, content, close, onSave } = props;
  const [editorState, setEditorState] = useState(
    () => EditorState.createEmpty(),
  );
  const [initContent, setInitContent] = useState<string>('');
  const [textAlignment, setTextAlignment] = useState<string>('left');
  const classes = useStyles();
  const [t] = useTranslation();

  const extendedBlockRenderMap = defaultBlockRenderMap();

  const onContentSave = () => {
    const value = DraftJsToHtml(editorState);
    if (initContent !== value) {
      onSave(value);
    }
  };

  const onStyleClick = (type: string) => {
    setEditorState(RichUtils.toggleInlineStyle(editorState, type));
  };

  useEffect(() => {
    if (content !== undefined) {
      setEditorState(EditorState.createWithContent(htmlToDraftJs(content, extendedBlockRenderMap)));
      setInitContent(content);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [content]);

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
        <Paper className={classes.main} style={style !== undefined ? style : {}}>
          <div className={classes.titlebox}>
            <Typography className={classes.title}>{title}</Typography>
          </div>
          <div className={classes.contentWrapper}>
            <div className={classes.header}>
              <Typography className={classes.textIcon} style={{ fontWeight: 'bold' }} onClick={() => onStyleClick('BOLD')}>B</Typography>
              <Typography className={classes.textIcon} style={{ fontStyle: 'italic' }} onClick={() => onStyleClick('ITALIC')}>I</Typography>
              <Typography className={classes.textIcon} style={{ textDecoration: 'underline' }} onClick={() => onStyleClick('UNDERLINE')}>U</Typography>
              <FormatAlignLeftIcon className={classes.alignIcon} onClick={() => setTextAlignment('left')} />
              <FormatAlignCenterIcon className={classes.alignIcon} onClick={() => setTextAlignment('center')} />
              <FormatAlignRightIcon className={classes.alignIcon} onClick={() => setTextAlignment('right')} />
            </div>
            <div className={classes.content}>
              <Editor
                editorState={editorState}
                onChange={setEditorState}
                blockRenderMap={extendedBlockRenderMap}
                textAlignment={textAlignment as any}
              />
            </div>
          </div>
          <div className={classes.footer}>
            <Button variant="contained" className={classes.button} onClick={close}>
              {t('main:closeButton')}
            </Button>
            <Button variant="contained" className={classes.button} color="primary" onClick={() => onContentSave()} disabled={initContent === DraftJsToHtml(editorState)}>
              {t('main:save')}
            </Button>
          </div>
        </Paper>
      </Fade>
    </Modal>
  );
};

TextEditorModal.defaultProps = {
  content: undefined,
  style: undefined,
};

export default TextEditorModal;
