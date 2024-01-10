import JSONEditorLib, { JSONEditorOptions } from "jsoneditor";
import { useRef } from "react";
import { useDeepCompareEffect, useMount } from "react-use";
import "jsoneditor/dist/jsoneditor.min.css";
import "./dark-theme.css";

interface JSONEditorProps extends JSONEditorOptions {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  json: any;
}

function JSONEditor({ json, ...options }: JSONEditorProps) {
  const ref = useRef<HTMLDivElement | null>(null);
  const editorRef = useRef<JSONEditorLib>();

  useMount(() => {
    if (!ref.current) {
      return;
    }

    const editor = new JSONEditorLib(ref.current, options);
    editor.set(json);
    editorRef.current = editor;

    return () => editor.destroy();
  });

  useDeepCompareEffect(() => {
    if (!editorRef.current) {
      return;
    }

    editorRef.current.set(json);
    editorRef.current.expandAll();
  }, [json]);

  return <div ref={ref} />;
}

export default JSONEditor;
