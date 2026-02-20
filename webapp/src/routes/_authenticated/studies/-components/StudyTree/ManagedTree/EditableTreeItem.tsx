/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import { Box, CircularProgress, TextField } from "@mui/material";
import { useEffect, useRef, useState } from "react";
import { editableRowStyles, textFieldStyles, treeNodeIcons } from "./styles";

interface EditableTreeItemProps {
  initialValue?: string;
  isEditing: boolean;
  isPending?: boolean;
  onSave: (name: string) => void;
  onCancel: () => void;
}

function EditableTreeItem({
  initialValue = "",
  isEditing,
  isPending = false,
  onSave,
  onCancel,
}: EditableTreeItemProps) {
  const [value, setValue] = useState(initialValue);
  const inputRef = useRef<HTMLInputElement>(null);
  const hasSavedRef = useRef(false);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      // Defer focus/select to the next animation frame so the browser has fully
      // painted the MUI tree item before we attempt to interact with the input.
      // Calling focus() synchronously after the render commit can silently fail
      // if the element is mid-transition and not yet interactable.
      requestAnimationFrame(() => {
        inputRef.current?.focus();
        inputRef.current?.select();
      });
    }
  }, [isEditing]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSave = () => {
    if (hasSavedRef.current) {
      return;
    }

    // Prevent double-save caused by Firefox triggering blur event when Enter is pressed
    hasSavedRef.current = true;
    const trimmedValue = value.trim();

    if (trimmedValue) {
      onSave(trimmedValue);
    } else {
      onCancel();
    }
  };

  const handleBlur = () => {
    handleSave();
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setValue(e.target.value);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    e.stopPropagation();

    if (e.key === "Enter") {
      e.preventDefault();
      handleSave();
    } else if (e.key === "Escape") {
      e.preventDefault();
      onCancel();
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (!isEditing) {
    return null;
  }

  const FolderIcon = treeNodeIcons.folder;

  return (
    <Box sx={editableRowStyles}>
      <FolderIcon sx={{ fontSize: "1.2rem", color: "info.main" }} />
      <TextField
        inputRef={inputRef}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        onBlur={handleBlur}
        size="small"
        disabled={isPending}
        sx={textFieldStyles}
        slotProps={{
          input: {
            endAdornment: isPending ? <CircularProgress size={16} sx={{ ml: 1 }} /> : null,
          },
        }}
      />
    </Box>
  );
}

export default EditableTreeItem;
