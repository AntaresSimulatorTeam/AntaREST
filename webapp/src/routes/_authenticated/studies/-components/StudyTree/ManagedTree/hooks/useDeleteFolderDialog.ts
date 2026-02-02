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

import { useState } from "react";
import type { DirectoryTreeNode } from "../types";
import { findDirectoryById } from "../utils";

interface DeleteDialogState {
  open: boolean;
  directoryId: string | null;
  folderName: string;
  hasChildren: boolean;
}

const INITIAL_STATE: DeleteDialogState = {
  open: false,
  directoryId: null,
  folderName: "",
  hasChildren: false,
};

export function useDeleteFolderDialog(directoryTree: DirectoryTreeNode) {
  const [state, setState] = useState<DeleteDialogState>(INITIAL_STATE);

  const openDialog = (directoryId: string) => {
    const directory = findDirectoryById(directoryTree, directoryId);
    if (!directory) {
      return;
    }

    setState({
      open: true,
      directoryId,
      folderName: directory.name,
      hasChildren: directory.children.length > 0,
    });
  };

  const closeDialog = () => {
    setState(INITIAL_STATE);
  };

  return {
    state,
    openDialog,
    closeDialog,
  };
}
