import { useEffect, useState } from "react";
import { Editor, EditorState, getDefaultKeyBinding, RichUtils } from "draft-js";
import { Box, styled, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import FormatListBulletedIcon from "@mui/icons-material/FormatListBulleted";
import FormatListNumberedIcon from "@mui/icons-material/FormatListNumbered";
import BasicModal from "../../../../common/BasicModal";
import { scrollbarStyle } from "../../../../../theme";
import { convertDraftJSToXML, convertXMLToDraftJS } from "./utils";

interface Props {
  open: boolean;
  onClose: () => void;
  content?: string;
  onSave: (content: string) => void;
}

export const EditorButton = styled(Typography)(({ theme }) => ({
  margin: theme.spacing(0, 2),
  fontSize: "1em",
  color: theme.palette.text.primary,
  cursor: "pointer",
  "&:hover": {
    color: theme.palette.secondary.main,
  },
}));

export const EditorIcon = {
  width: "20px",
  height: "auto",
  color: "text.primary",
  cursor: "pointer",
  my: 0,
  mx: 2,
  "&:hover": {
    color: "secondary.main",
  },
};

function NoteEditorModal(props: Props) {
  const [t] = useTranslation();
  const { open, onClose, content, onSave } = props;

  const [editorState, setEditorState] = useState(() =>
    EditorState.createEmpty()
  );
  const [initContent, setInitContent] = useState<string>("");

  const onContentSave = () => {
    const value = convertDraftJSToXML(editorState);
    if (initContent !== value) {
      onSave(value);
    }
  };

  const onStyleClick = (type: string) => {
    setEditorState(RichUtils.toggleInlineStyle(editorState, type));
  };

  const toggleBulletPoints = (type: string) => {
    setEditorState(RichUtils.toggleBlockType(editorState, type));
  };

  const handleKeyBindings = (e: any) => {
    if (e.keyCode === 9) {
      const newEditorState = RichUtils.onTab(e, editorState, 6 /* maxDepth */);
      if (newEditorState !== editorState) {
        setEditorState(newEditorState);
      }
    }
    getDefaultKeyBinding(e);
  };

  useEffect(() => {
    if (content !== undefined) {
      setEditorState(
        EditorState.createWithContent(convertXMLToDraftJS(content))
      );
      setInitContent(content);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [content]);

  return (
    <BasicModal
      title={t("singlestudy:userNote")}
      open={open}
      onClose={onClose}
      closeButtonLabel={t("main:cancelButton")}
      actionButtonLabel={t("main:save")}
      onActionButtonClick={onContentSave}
      closeColor="secondary"
      rootStyle={{
        width: "600px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "flex-start",
        alignItems: "center",
        boxSizing: "border-box",
      }}
    >
      <Box
        width="100%"
        height="500px"
        display="flex"
        flexDirection="column"
        justifyContent="flex-start"
        alignItems="center"
        p={2}
        boxSizing="border-box"
        sx={{ overflowX: "hidden", overflowY: "auto", ...scrollbarStyle }}
      >
        <Box
          width="100%"
          height="50px"
          display="flex"
          flexDirection="row"
          justifyContent="flex-start"
          alignItems="center"
        >
          <EditorButton
            sx={{ fontWeight: "bold" }}
            onClick={() => onStyleClick("BOLD")}
          >
            B
          </EditorButton>
          <EditorButton
            sx={{ fontStyle: "italic" }}
            onClick={() => onStyleClick("ITALIC")}
          >
            I
          </EditorButton>
          <EditorButton
            sx={{ textDecoration: "underline" }}
            onClick={() => onStyleClick("UNDERLINE")}
          >
            U
          </EditorButton>
          <FormatListBulletedIcon
            sx={{ ...EditorIcon }}
            onClick={() => toggleBulletPoints("unordered-list-item")}
          />
          <FormatListNumberedIcon
            sx={{ ...EditorIcon }}
            onClick={() => toggleBulletPoints("ordered-list-item")}
          />
        </Box>
        <Box
          sx={{
            p: 3,
            height: "calc(100% - 40px)",
            width: "100%",
            boxSizing: "border-box",
            overflow: "auto",
            ...scrollbarStyle,
          }}
        >
          <Editor
            editorState={editorState}
            onChange={setEditorState}
            onTab={handleKeyBindings}
            textAlignment="left"
          />
        </Box>
      </Box>
    </BasicModal>
  );
}

NoteEditorModal.defaultProps = {
  content: undefined,
};

export default NoteEditorModal;
