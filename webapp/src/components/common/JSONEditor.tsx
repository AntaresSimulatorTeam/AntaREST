import { useEffect, useRef } from "react";
import { useMount } from "react-use";
import {
  JSONEditor as JSONEditorLib,
  type JSONEditorPropsOptional,
} from "vanilla-jsoneditor";
import "vanilla-jsoneditor/themes/jse-theme-dark.css";

export type JSONEditorProps = JSONEditorPropsOptional;

function JSONEditor(props: JSONEditorProps) {
  const targetRef = useRef<HTMLDivElement>(null!);
  const editorRef = useRef<JSONEditorLib | null>(null);

  useMount(() => {
    const editor = new JSONEditorLib({ target: targetRef.current, props });
    editorRef.current = editor;
    return () => editor.destroy();
  });

  useEffect(() => {
    editorRef.current?.updateProps(props);
  }, [props]);

  return <div ref={targetRef} className="jse-theme-dark" />;
}

export default JSONEditor;
