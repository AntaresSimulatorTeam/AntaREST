import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { AxiosError } from "axios";
import { Box, Button, Divider, Paper, styled, Typography } from "@mui/material";
import StickyNote2OutlinedIcon from "@mui/icons-material/StickyNote2Outlined";
import { ContentState, Editor, EditorState } from "draft-js";
import "draft-js/dist/Draft.css";
import {
  editComments,
  getComments,
  getStudySynthesis,
} from "../../../../../services/api/study";
import { convertXMLToDraftJS } from "./utils";
import { StudyMetadata } from "../../../../../common/types";
import { scrollbarStyle } from "../../../../../theme";
import enqueueErrorSnackbar from "../../../../common/ErrorSnackBar";
import NoteEditorModal from "./NoteEditorModal";
import SimpleLoader from "../../../../common/loaders/SimpleLoader";

const Root = styled(Box)(({ theme }) => ({
  flex: "0 0 40%",
  height: "100%",
  display: "flex",
  flexDirection: "column",
  justifyContent: "flex-start",
  alignItems: "center",
}));

const Note = styled(Box)(({ theme }) => ({
  flex: "0 0 70%",
  width: "100%",
  display: "flex",
  flexDirection: "column",
  justifyContent: "flex-start",
  alignItems: "center",
  padding: theme.spacing(2),
  paddingTop: 0,
}));

const NoteHeader = styled(Box)(({ theme }) => ({
  display: "flex",
  justifyContent: "flex-start",
  alignItems: "center",
  width: "100%",
  height: "60px",
}));

const NoteFooter = NoteHeader;

const EditorContainer = styled(Box)(({ theme }) => ({
  display: "flex",
  justifyContent: "flex-start",
  alignItems: "flex-start",
  width: "100%",
  height: 0,
  flex: 1,
  padding: theme.spacing(0),
  overflow: "hidden",
}));

const FigureInfoContainer = styled(Box)(({ theme }) => ({
  display: "flex",
  justifyContent: "center",
  alignItems: "flex-start",
  width: "100%",
  flexGrow: 1,
  padding: theme.spacing(2),
}));

const FigureInfo = styled(Paper)(({ theme }) => ({
  backgroundColor: "rgba(36, 207, 157, 0.05)",
  display: "flex",
  flexDirection: "column",
  justifyContent: "center",
  alignItems: "center",
  width: "87px",
  height: "96px",
  margin: theme.spacing(0, 1),
}));

function Figure({ title, data }: { title: string; data: number }) {
  return (
    <FigureInfo>
      <Typography
        variant="h4"
        fontStyle="normal"
        fontWeight={400}
        fontSize="34px"
        lineHeight="123.5%"
      >
        {data}
      </Typography>
      <Typography
        fontStyle="normal"
        fontWeight={400}
        fontSize="16px"
        lineHeight="175%"
        letterSpacing="0.15px"
      >
        {title}
      </Typography>
    </FigureInfo>
  );
}

interface Props {
  // eslint-disable-next-line react/no-unused-prop-types
  study: StudyMetadata | undefined;
}

export default function Notes(props: Props) {
  const { study } = props;
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const [editorState, setEditorState] = useState(() =>
    EditorState.createEmpty()
  );
  const [editionMode, setEditionMode] = useState<boolean>(false);
  const [content, setContent] = useState<string>("");
  const [loaded, setLoaded] = useState(false);
  const [nbAreas, setNbAreas] = useState<number>(0);
  const [nbLinks, setNbLinks] = useState<number>(0);

  const onSave = async (newContent: string) => {
    if (study) {
      try {
        await editComments(study.id, newContent);
        setEditorState(
          EditorState.createWithContent(convertXMLToDraftJS(newContent))
        );
        setContent(newContent);
        enqueueSnackbar(t("singlestudy:commentsSaved"), { variant: "success" });
        setEditionMode(false);
      } catch (e) {
        enqueueErrorSnackbar(
          enqueueSnackbar,
          t("singlestudy:commentsNotSaved"),
          e as AxiosError
        );
      }
    }
  };

  useEffect(() => {
    const init = async () => {
      if (study) {
        try {
          const data = await getComments(study?.id);
          setEditorState(
            EditorState.createWithContent(convertXMLToDraftJS(data))
          );
          setContent(data);
        } catch (e) {
          setEditorState(
            EditorState.createWithContent(
              ContentState.createFromText(t("singlestudy:fetchCommentsError"))
            )
          );
        } finally {
          setLoaded(true);
        }
      }
    };
    init();
    return () => setContent("");
  }, [study, t]);

  useEffect(() => {
    (async () => {
      if (study) {
        try {
          const tmpSynth = await getStudySynthesis(study.id);
          const areas = Object.keys(tmpSynth.areas).map(
            (elm) => tmpSynth.areas[elm]
          );
          const links = areas
            .map((elm) => Object.keys(elm.links).length)
            .reduce(
              (prevValue: number, currentValue: number) =>
                prevValue + currentValue
            );
          setNbAreas(areas.length);
          setNbLinks(links);
        } catch (e) {
          enqueueErrorSnackbar(
            enqueueSnackbar,
            t("singlestudy:getAreasInfo"),
            e as AxiosError
          );
        }
      }
    })();
  }, [enqueueSnackbar, study, t]);
  return (
    <Root>
      <Note>
        <NoteHeader>
          <StickyNote2OutlinedIcon sx={{ color: "text.secondary", mr: 1 }} />
          <Typography color="text.secondary">
            {t("singlestudy:notes")}
          </Typography>
        </NoteHeader>
        <EditorContainer sx={{ overflowY: "auto", ...scrollbarStyle }}>
          {!loaded && <SimpleLoader />}
          {loaded && (
            <Editor
              readOnly={!editionMode}
              editorState={editorState}
              onChange={setEditorState}
              textAlignment="left"
            />
          )}
        </EditorContainer>
        <NoteFooter>
          <Button
            variant="text"
            color="secondary"
            onClick={() => setEditionMode(true)}
          >
            {t("main:edit")}
          </Button>
        </NoteFooter>
      </Note>
      <Divider sx={{ width: "98%", height: "1px", bgcolor: "divider" }} />
      <FigureInfoContainer>
        <Figure title={t("singlestudy:area")} data={nbAreas} />
        <Figure title={t("singlestudy:link")} data={nbLinks} />
      </FigureInfoContainer>
      {editionMode && (
        <NoteEditorModal
          open={editionMode}
          content={content}
          onClose={() => setEditionMode(false)}
          onSave={onSave}
        />
      )}
    </Root>
  );
}
