import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { AxiosError } from "axios";
import { Box, Button, Typography } from "@mui/material";
import StickyNote2OutlinedIcon from "@mui/icons-material/StickyNote2Outlined";
import { ContentState, Editor, EditorState } from "draft-js";
import "draft-js/dist/Draft.css";
import { editComments, getComments } from "../../../../../services/api/study";
import { convertXMLToDraftJS } from "./utils";
import { StudyMetadata } from "../../../../../common/types";
import { scrollbarStyle } from "../../../../../theme";
import enqueueErrorSnackbar from "../../../../common/ErrorSnackBar";
import NoteEditorModal from "./NoteEditorModal";
import SimpleLoader from "../../../../common/loaders/SimpleLoader";

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
  return (
    <Box
      sx={{
        flex: "0 0 40%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "flex-start",
        alignItems: "center",
      }}
    >
      <Box
        sx={{
          flex: "0 0 70%",
          width: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "flex-start",
          alignItems: "center",
          p: 2,
        }}
      >
        <Box
          display="flex"
          justifyContent="flex-start"
          alignItems="center"
          width="100%"
          height="60px"
        >
          <StickyNote2OutlinedIcon sx={{ color: "text.secondary", mr: 1 }} />
          <Typography color="text.secondary">
            {t("singlestudy:userNote")}
          </Typography>
        </Box>
        <Box
          display="flex"
          justifyContent="flex-start"
          alignItems="center"
          width="100%"
          height={0}
          flex={1}
          p={0}
          overflow="hidden"
          sx={{ overflowY: "auto", ...scrollbarStyle }}
        >
          {!loaded && <SimpleLoader />}
          {loaded && (
            <Editor
              readOnly={!editionMode}
              editorState={editorState}
              onChange={setEditorState}
              textAlignment="left"
            />
          )}
        </Box>
        <Box
          display="flex"
          justifyContent="flex-start"
          alignItems="center"
          width="100%"
          height="60px"
        >
          <Button
            variant="text"
            color="secondary"
            onClick={() => setEditionMode(true)}
          >
            {t("main:edit")}
          </Button>
        </Box>
      </Box>
      {editionMode && (
        <NoteEditorModal
          open={editionMode}
          content={content}
          onClose={() => setEditionMode(false)}
          onSave={onSave}
        />
      )}
    </Box>
  );
}
