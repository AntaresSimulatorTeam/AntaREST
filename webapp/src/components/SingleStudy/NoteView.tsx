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
import enqueueErrorSnackbar from '../ui/ErrorSnackBar';
import TextEditorModal from '../ui/TextEditorModal';
import { editComments, getComments } from '../../services/api/study';
import { convertXMLToHTML, defaultBlockRenderMap, htmlToDraftJs, xmlToJson } from '../ui/Utils';

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
      alignItems: 'center',
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

  const extendedBlockRenderMap = defaultBlockRenderMap();

  const onSave = async (newContent: string) => {
    try {
      await editComments(studyId, newContent);
      setEditorState(EditorState.createWithContent(htmlToDraftJs(newContent, extendedBlockRenderMap)));
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
        //console.log('XML TO JSON: ', xmlToJson(data));
        //const xmlToHtml = convertXMLToHTML(data);
        const xmlToHtml = convertXMLToHTML(`
        <?xml version="1.0" encoding="UTF-8"?>
        <richtext version="1.0.0.0" xmlns="http://www.wxwidgets.org">
          <paragraphlayout textcolor="#000000" fontpointsize="9" fontfamily="70" fontstyle="90" fontweight="400" fontunderlined="0" fontface="Segoe UI" alignment="1" parspacingafter="10" parspacingbefore="0" linespacing="10" margin-left="5,4098" margin-right="5,4098" margin-top="5,4098" margin-bottom="5,4098">
            <paragraph>
              <text>This is a test.</text>
            </paragraph>
            <paragraph alignment="2">
              <text>There is centered.</text>
            </paragraph>
            <paragraph alignment="2">
              <text fontweight="700">And bold</text>
            </paragraph>
            <paragraph alignment="3">
              <text fontweight="400">To the right and</text>
              <text fontstyle="93" fontweight="400">" there in italic"</text>
            </paragraph>
            <paragraph alignment="1">
              <text></text>
            </paragraph>
            <paragraph alignment="1" leftindent="200" leftsubindent="0">
              <text>indenting twice</text>
            </paragraph>
            <paragraph alignment="1">
              <text></text>
            </paragraph>
            <paragraph alignment="1">
              <text fontunderlined="1">This is underlined.</text>
              <text fontunderlined="0">" "</text>
              <text fontstyle="93" fontweight="700" fontunderlined="0">"And now a multilined "</text>
            </paragraph>
            <paragraph alignment="1">
              <text fontstyle="93" fontweight="700" fontunderlined="0">bold and italic</text>
            </paragraph>
            <paragraph alignment="1">
              <text></text>
            </paragraph>
            <paragraph alignment="1">
              <text fontstyle="90">Some bullet points:</text>
            </paragraph>
            <paragraph alignment="1" leftindent="60" leftsubindent="60" bulletstyle="512" bulletnumber="1" bulletname="standard/circle" liststyle="Bullet List">
              <text>first</text>
            </paragraph>
            <paragraph alignment="1" leftindent="60" leftsubindent="60" bulletstyle="512" bulletnumber="2" bulletname="standard/circle" liststyle="Bullet List">
              <text>second</text>
            </paragraph>
            <paragraph alignment="1" leftindent="60" leftsubindent="60" bulletstyle="512" bulletnumber="3" bulletname="standard/circle" liststyle="Bullet List">
              <text>third</text>
            </paragraph>
            <paragraph alignment="1">
              <text></text>
            </paragraph>
            <paragraph alignment="1">
              <text>And list :</text>
            </paragraph>
            <paragraph alignment="1" leftindent="60" leftsubindent="60" bulletstyle="4353" bulletnumber="1" liststyle="Numbered List">
              <text>a</text>
            </paragraph>
            <paragraph alignment="1" leftindent="60" leftsubindent="60" bulletstyle="4353" bulletnumber="2" liststyle="Numbered List">
              <text>b</text>
            </paragraph>
            <paragraph alignment="1" leftindent="60" leftsubindent="60" bulletstyle="4353" bulletnumber="3" liststyle="Numbered List">
              <text>c</text>
            </paragraph>
          </paragraphlayout>
        </richtext>`);
        console.log('XML TO HTML: ', xmlToHtml);
        setEditorState(EditorState.createWithContent(htmlToDraftJs(xmlToHtml, extendedBlockRenderMap)));
        setContent(data);
      } catch (e) {
        enqueueErrorSnackbar(enqueueSnackbar, t('singlestudy:fetchCommentsError'), e as AxiosError);
      }
    };
    init();
  // eslint-disable-next-line react-hooks/exhaustive-deps
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
            blockRenderMap={extendedBlockRenderMap}
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
