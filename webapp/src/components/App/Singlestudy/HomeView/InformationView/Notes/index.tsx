import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { AxiosError } from "axios";
import { Box, Button, Divider, styled, Typography } from "@mui/material";
import StickyNote2OutlinedIcon from "@mui/icons-material/StickyNote2Outlined";
import LinearScaleIcon from "@mui/icons-material/LinearScale";
import StorageIcon from "@mui/icons-material/Storage";
import HubIcon from "@mui/icons-material/Hub";
import { Editor, EditorState } from "draft-js";
import "draft-js/dist/Draft.css";
import {
  editComments,
  getComments,
  getStudyDiskUsage,
} from "../../../../../../services/api/study";
import { convertSize, convertXMLToDraftJS, getColorForSize } from "./utils";
import { StudyMetadata } from "../../../../../../common/types";
import NoteEditorModal from "./NodeEditorModal";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import usePromiseWithSnackbarError from "../../../../../../hooks/usePromiseWithSnackbarError";
import DetailsList from "./DetailsList";
import { getAreas, getLinks } from "../../../../../../redux/selectors";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";

const Root = styled(Box)(() => ({
  flex: "0 0 40%",
  height: "100%",
  display: "flex",
  flexDirection: "column",
  justifyContent: "flex-start",
  alignItems: "center",
  overflow: "hidden",
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

const NoteHeader = styled(Box)(() => ({
  display: "flex",
  justifyContent: "flex-start",
  alignItems: "center",
  width: "100%",
  height: "60px",
  boxSizing: "border-box",
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
  overflow: "auto",
}));

interface Props {
  study: StudyMetadata;
}

function Notes({ study }: Props) {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [editorState, setEditorState] = useState(() =>
    EditorState.createEmpty(),
  );
  const [editionMode, setEditionMode] = useState(false);
  const [content, setContent] = useState("");
  const areas = useAppSelector((state) => getAreas(state, study.id));
  const links = useAppSelector((state) => getLinks(state, study.id));

  const res = usePromiseWithSnackbarError(
    async () => {
      const [comments, diskUsage] = await Promise.all([
        getComments(study.id),
        getStudyDiskUsage(study.id),
      ]);

      return { comments, diskUsage };
    },
    {
      errorMessage: t("studies.error.retrieveData"),
      deps: [study?.id],
    },
  );

  useEffect(() => {
    if (!res.data) {
      return;
    }
    const { comments } = res.data;
    setEditorState(
      EditorState.createWithContent(convertXMLToDraftJS(comments)),
    );
    setContent(comments);
  }, [res.data]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSave = async (newContent: string) => {
    try {
      await editComments(study.id, newContent);
      setEditorState(
        EditorState.createWithContent(convertXMLToDraftJS(newContent)),
      );
      setContent(newContent);
      enqueueSnackbar(t("study.success.commentsSaved"), {
        variant: "success",
      });
      setEditionMode(false);
    } catch (e) {
      enqueueErrorSnackbar(t("study.error.commentsNotSaved"), e as AxiosError);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Root>
      <UsePromiseCond
        response={res}
        ifResolved={(data) => (
          <>
            <Note>
              <NoteHeader>
                <StickyNote2OutlinedIcon
                  sx={{ color: "text.secondary", mr: 1 }}
                />
                <Typography color="text.secondary">
                  {t("study.notes")}
                </Typography>
              </NoteHeader>
              <EditorContainer>
                <Editor
                  readOnly={!editionMode}
                  editorState={editorState}
                  onChange={setEditorState}
                  textAlignment="left"
                />
              </EditorContainer>
              <NoteFooter>
                <Button
                  variant="text"
                  color="secondary"
                  onClick={() => setEditionMode(true)}
                >
                  {t("global.edit")}
                </Button>
              </NoteFooter>
            </Note>
            <Divider sx={{ width: "98%", height: "1px", bgcolor: "divider" }} />
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                width: 1,
                height: 1,
              }}
            >
              <DetailsList
                items={[
                  {
                    content: convertSize(data.diskUsage),
                    label: t("study.diskUsage"),
                    icon: StorageIcon,
                    iconColor: getColorForSize(data.diskUsage),
                  },
                  {
                    content: areas.length,
                    label: t("study.areas"),
                    icon: HubIcon,
                  },
                  {
                    content: links.length,
                    label: t("study.links"),
                    icon: LinearScaleIcon,
                  },
                ]}
              />
            </Box>
          </>
        )}
      />

      {editionMode && (
        <NoteEditorModal
          open={editionMode}
          content={content}
          onClose={() => setEditionMode(false)}
          onSave={handleSave}
        />
      )}
    </Root>
  );
}

export default Notes;
