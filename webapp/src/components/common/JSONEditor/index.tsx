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
import JSONEditorClass, { type JSONEditorOptions, type HistoryItem } from "jsoneditor";
import { useMemo, useRef } from "react";
import { useDeepCompareEffect, useMount } from "react-use";
import "jsoneditor/dist/jsoneditor.min.css";
import "./dark-theme.css";
import type { PromiseAny } from "../../../utils/tsUtils";
import useAutoUpdateRef from "../../../hooks/useAutoUpdateRef";
import { createSaveButton } from "./utils";
import * as R from "ramda";
import * as RA from "ramda-adjunct";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import { toError } from "../../../utils/fnUtils";
import { Box } from "@mui/material";

export interface JSONEditorProps extends JSONEditorOptions {
  json: any;
  onSave?: (json: any) => PromiseAny;
  onSaveSuccessful?: (json: any) => any;
}

function JSONEditor(props: JSONEditorProps) {
  const { json, onSave, onSaveSuccessful, ...options } = props;
  const ref = useRef<HTMLDivElement | null>(null);
  const editorRef = useRef<JSONEditorClass>();
  const onSaveRef = useAutoUpdateRef(onSave);
  const callbackOptionsRef = useAutoUpdateRef<Partial<JSONEditorOptions>>(
    R.pickBy(RA.isFunction, options),
  );
  const saveBtn = useMemo(() => createSaveButton(handleSaveClick), []);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

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

  async function handleSaveClick() {
    const onSave = onSaveRef.current;
    const editor = editorRef.current;

    if (onSave && editor) {
      let json;

      try {
        json = editor.get();
      } catch (err) {
        enqueueErrorSnackbar("Invalid JSON", toError(err));
        return;
      }

      try {
        await onSave(json);

        updateSaveState(false);
        onSaveSuccessful?.(json);

        presentHistoryItem.current = editor?.history?.history?.[editor.history.index] ?? null;
      } catch (err) {
        enqueueErrorSnackbar("test", toError(err));
      }
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
      // The save button is added to the menu only when the `onSave` callback is provided
      onSaveRef.current &&
      editor &&
      ["tree", "form", "code", "text"].includes(editor.getMode())
    ) {
      updateSaveState(false);
      editor.menu.append(saveBtn);
    }
  }

  function updateSaveState(enable: boolean) {
    // Update the save button style
    saveBtn.style.opacity = enable ? "1" : "0.1";
    saveBtn.disabled = !enable;

    // Changing the mode resets undo/redo history and undo/redo are not available in all modes.
    // So the change mode mode button is disabled when the JSON is dirty.

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
    <Box
      sx={{
        height: 1,
        overflow: "auto", // Fix when parent use `flex-direction: "column"`
      }}
      ref={ref}
    />
  );
}

export default JSONEditor;
