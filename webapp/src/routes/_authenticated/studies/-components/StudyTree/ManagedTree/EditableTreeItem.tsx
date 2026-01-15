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

import { TextField } from "@mui/material";
import { useEffect, useRef, useState } from "react";
import TreeItemEnhanced from "@/components/TreeItemEnhanced";
import { editableTreeItemStyles, textFieldStyles, treeNodeIcons } from "./styles";

interface EditableTreeItemProps {
  itemId: string;
  initialValue?: string;
  isEditing: boolean;
  onSave: (name: string) => void;
  onCancel: () => void;
}

function EditableTreeItem({
  itemId,
  initialValue = "",
  isEditing,
  onSave,
  onCancel,
}: EditableTreeItemProps) {
  const [value, setValue] = useState(initialValue);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      // Small delay to ensure the tree item is rendered
      setTimeout(() => {
        inputRef.current?.focus();
        inputRef.current?.select();
      }, 50);
    }
  }, [isEditing]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSave = () => {
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

  return (
    <TreeItemEnhanced
      itemId={itemId}
      label={
        <TextField
          inputRef={inputRef}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
          size="small"
          onClick={(e) => e.stopPropagation()}
          onMouseDown={(e) => e.stopPropagation()}
          fullWidth
          sx={textFieldStyles}
        />
      }
      slots={{
        expandIcon: treeNodeIcons.folder,
      }}
      sx={editableTreeItemStyles}
    />
  );
}

export default EditableTreeItem;
