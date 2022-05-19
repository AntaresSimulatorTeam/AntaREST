import { useEffect, useState } from "react";
import { Editor, EditorState, getDefaultKeyBinding, RichUtils } from "draft-js";
import { Button } from "@mui/material";
import { useTranslation } from "react-i18next";
import FormatListBulletedIcon from "@mui/icons-material/FormatListBulleted";
import FormatListNumberedIcon from "@mui/icons-material/FormatListNumbered";
import { convertDraftJSToXML, convertXMLToDraftJS } from "../utils";
import BasicDialog from "../../../../../common/dialogs/BasicDialog";
import {
  EditorButton,
  EditorContainer,
  EditorIcon,
  Header,
  Root,
} from "./style";

interface Props {
  open: boolean;
  onClose: () => void;
  content?: string;
  onSave: (content: string) => void;
}

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

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
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
    <BasicDialog
      open={open}
      onClose={onClose}
      title={t("global:study.notes")}
      contentProps={{
        sx: {
          width: "100%",
          minHeight: "600px",
          p: 0,
          overflow: "hidden",
        },
      }}
      fullWidth
      maxWidth="lg"
      actions={
        <>
          <Button variant="text" color="primary" onClick={onClose}>
            {t("global:global.cancel")}
          </Button>
          <Button
            sx={{ mx: 2 }}
            color="primary"
            variant="contained"
            onClick={onContentSave}
          >
            {t("global:global.save")}
          </Button>
        </>
      }
    >
      <Root>
        <Header>
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
        </Header>
        <EditorContainer>
          <Editor
            editorState={editorState}
            onChange={setEditorState}
            onTab={handleKeyBindings}
            textAlignment="left"
          />
        </EditorContainer>
      </Root>
    </BasicDialog>
  );
}

NoteEditorModal.defaultProps = {
  content: undefined,
};

export default NoteEditorModal;
