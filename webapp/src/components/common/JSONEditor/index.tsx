/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
import { mergeSxProp } from "@/utils/muiUtils";
import { Box, setRef, type SxProps, type Theme } from "@mui/material";
import JSONEditorClass, { type HistoryItem, type JSONEditorOptions } from "jsoneditor";
import "jsoneditor/dist/jsoneditor.min.css";
import * as R from "ramda";
import * as RA from "ramda-adjunct";
import { useEffect, useMemo, useRef, useState } from "react";
import { useDeepCompareEffect, useMount, useUpdateEffect } from "react-use";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import useUpdatedRef from "../../../hooks/useUpdatedRef";
import { toError } from "../../../utils/fnUtils";
import type { PromiseAny } from "../../../utils/tsUtils";
import BackdropLoading from "../loaders/BackdropLoading";
import "./dark-theme.css";
import { createSaveButton } from "./utils";

export interface JSONApi {
  save: VoidFunction;
}

export interface JSONState {
  isDirty: boolean;
  isSaving: boolean;
}

export interface JSONEditorProps extends JSONEditorOptions {
  json: any;
  onSave?: (json: any) => PromiseAny;
  onSaveSuccessful?: (json: any) => any;
  sx?: SxProps<Theme>;
  hideSaveButton?: boolean;
  apiRef?: React.Ref<JSONApi>;
  onStateChange?: (state: JSONState) => void;
}

function JSONEditor({
  json,
  onSave,
  onSaveSuccessful,
  sx,
  hideSaveButton,
  apiRef,
  onStateChange,
  ...options
}: JSONEditorProps) {
  const ref = useRef<HTMLDivElement | null>(null);
  const editorRef = useRef<JSONEditorClass>();
  const onSaveRef = useUpdatedRef(onSave);
  const callbackOptionsRef = useUpdatedRef<Partial<JSONEditorOptions>>(
    R.pickBy(RA.isFunction, options),
  );
  const saveBtn = useMemo(() => createSaveButton(handleSave), []);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [isDirty, setIsDirty] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  /**
   * The history item corresponding to the saved JSON.
   * Only for some modes.
   */
  const presentHistoryItem = useRef<HistoryItem | null>(null);

  // Initialize the JSON editor
  useMount(() => {
    if (!ref.current) {
      return;
    }

    const editor = new JSONEditorClass(ref.current, {
      ...options,
      ...callbackOptionsRef.current,
      onChange: handleChange,
      onModeChange: handleModeChange,
    });
    editor.set(json);

    editorRef.current = editor;

    initSave();

    return () => editor.destroy();
  });

  // Update JSON when `json` prop change
  useDeepCompareEffect(() => {
    const editor = editorRef.current;

    if (editor) {
      editor.set(json);
      editor.expandAll?.();
    }
  }, [json]);

  useEffect(() => {
    setRef(apiRef, {
      save: handleSave,
    });
  });

  useUpdateEffect(() => {
    onStateChange?.({ isDirty, isSaving });
  }, [isDirty, isSaving]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  function handleChange() {
    callbackOptionsRef.current.onChange?.();

    // Update the save button state

    const editor = editorRef.current;

    // Use undo/redo history to determine if the JSON is dirty
    if (editor?.history?.history) {
      updateSaveState(
        presentHistoryItem.current !== (editor.history.history[editor.history.index] ?? null),
      );
    } else {
      updateSaveState(true);
    }
  }

  function handleModeChange(...args: Parameters<NonNullable<JSONEditorOptions["onModeChange"]>>) {
    callbackOptionsRef.current.onModeChange?.(...args);
    // Menu is reset when the mode changes
    initSave();
  }

  async function handleSave() {
    const onSave = onSaveRef.current;
    const editor = editorRef.current;

    if (onSave && editor) {
      setIsSaving(true);

      try {
        const json = editor.get();

        await onSave(json);

        updateSaveState(false);
        onSaveSuccessful?.(json);

        presentHistoryItem.current = editor?.history?.history?.[editor.history.index] ?? null;
      } catch (err) {
        enqueueErrorSnackbar("Cannot save JSON changes", toError(err));
      }

      setIsSaving(false);
    }
  }

  ////////////////////////////////////////////////////////////////
  // Save
  ////////////////////////////////////////////////////////////////

  function initSave() {
    const editor = editorRef.current;

    presentHistoryItem.current = null;
    saveBtn.remove();

    if (
      !hideSaveButton &&
      // The save button is added to the menu only when the `onSave` callback is provided
      onSaveRef.current &&
      editor &&
      ["tree", "form", "code", "text"].includes(editor.getMode())
    ) {
      editor.menu.append(saveBtn);
    }

    updateSaveState(false);
  }

  function updateSaveState(enable: boolean) {
    setIsDirty(enable);

    // Update the save button style
    saveBtn.style.opacity = enable ? "1" : "0.1";
    saveBtn.disabled = !enable;

    // Changing the mode resets undo/redo history and undo/redo are not available in all modes.
    // So the change mode button is disabled when the JSON is dirty.

    const editorModeBtn = editorRef.current?.menu.querySelector("button.jsoneditor-modes");

    if (enable) {
      editorModeBtn?.setAttribute("disabled", "");
    } else {
      editorModeBtn?.removeAttribute("disabled");
    }
  }

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <BackdropLoading open={isSaving}>
      <Box
        sx={mergeSxProp(
          {
            overflow: "auto", // Fix when parent use `flex-direction: "column"`
          },
          sx,
        )}
        ref={ref}
      />
    </BackdropLoading>
  );
}

export default JSONEditor;
