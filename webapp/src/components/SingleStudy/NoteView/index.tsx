/* eslint-disable jsx-a11y/no-static-element-interactions */
/* eslint-disable jsx-a11y/click-events-have-key-events */
import React, { useEffect, useState } from 'react';
import { AxiosError } from 'axios';
import { Editor, EditorState } from 'draft-js';
import 'draft-js/dist/Draft.css';
import {
  makeStyles,
  createStyles,
  Theme,
  Paper,
  Typography,
} from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import CreateIcon from '@material-ui/icons/Create';
import enqueueErrorSnackbar from '../../ui/ErrorSnackBar';
import TextEditorModal from './TextEditorModal';
import { editComments, getComments } from '../../../services/api/study';
import { convertXMLToDraftJS } from './utils';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      width: '100%',
      height: '48%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      backgroundColor: 'white',
      margin: theme.spacing(1),
      boxSizing: 'border-box',
    },
    header: {
      width: '100%',
      height: '40px',
      boxSizing: 'border-box',
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      backgroundColor: theme.palette.primary.main,
      borderTopLeftRadius: theme.shape.borderRadius,
      borderTopRightRadius: theme.shape.borderRadius,
      paddingLeft: theme.spacing(2),
    },
    title: {
      fontWeight: 'bold',
      color: 'white',
    },
    main: {
      flex: 1,
      width: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
    },
    headerButton: {
      width: '100%',
      height: '40px',
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-end',
      alignItems: 'center',
      paddingRight: theme.spacing(3),
    },
    editButton: {
      width: '20px',
      height: 'auto',
      color: theme.palette.primary.main,
      cursor: 'pointer',
      '&:hover': {
        color: theme.palette.secondary.main,
      },
    },
    content: {
      flex: 1,
      width: '100%',
      padding: theme.spacing(2, 2),
      height: 0,
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'flex-start',
      overflowY: 'auto',
      overflowX: 'hidden',
      boxSizing: 'border-box',
    },
  }));

interface Props {
    studyId: string;
}

const NoteView = (props: Props) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { studyId } = props;
  const [editorState, setEditorState] = useState(
    () => EditorState.createEmpty(),
  );
  const [editionMode, setEditionMode] = useState<boolean>(false);
  const [content, setContent] = useState<string>('');

  const onSave = async (newContent: string) => {
    try {
      await editComments(studyId, newContent);
      setEditorState(EditorState.createWithContent(convertXMLToDraftJS(newContent)));
      setContent(newContent);
      setEditionMode(false);
      enqueueSnackbar(t('singlestudy:commentsSaved'), { variant: 'success' });
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('singlestudy:commentsNotSaved'), e as AxiosError);
    }
  };

  useEffect(() => {
    const init = async () => {
      try {
        const data = await getComments(studyId);
        setEditorState(EditorState.createWithContent(convertXMLToDraftJS(data)));
        setContent(data);
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('singlestudy:fetchCommentsError'), e as AxiosError);
      }
    };
    init();
    return () => setContent('');
  }, [enqueueSnackbar, studyId, t]);

  return (
    <Paper className={classes.root}>
      <div className={classes.header}>
        <Typography className={classes.title}>{t('singlestudy:notes')}</Typography>
      </div>
      <div className={classes.main}>
        <div className={classes.headerButton}>
          <CreateIcon className={classes.editButton} onClick={() => setEditionMode(true)} />
        </div>
        <div className={classes.content}>
          <Editor
            readOnly={!editionMode}
            editorState={editorState}
            onChange={setEditorState}
            textAlignment="left"
          />
        </div>
      </div>
      {
       editionMode && (
       <TextEditorModal
         isOpen={editionMode}
         title="Comments"
         content={content}
         close={() => setEditionMode(false)}
         onSave={onSave}
       />
       )}
    </Paper>
  );
};

export default NoteView;
