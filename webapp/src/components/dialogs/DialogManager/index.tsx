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

import BasicDialog from "@/components/dialogs/BasicDialog";
import ConfirmationDialog from "@/components/dialogs/ConfirmationDialog";
import useOrderedState from "@/hooks/useOrderedState";
import { useCallback } from "react";
import { DialogManagerContext } from "./DialogManagerContext";
import type { DialogManagerApi, SetDialogOptions } from "./types";

export interface DialogManagerProps {
  children: React.ReactNode;
}

function getDialogProps<T extends SetDialogOptions>(options: T) {
  const { type, ...props } = options;
  return { ...props, open: true };
}

function getDialog(options: SetDialogOptions, key: string) {
  if (options.type === "confirmation") {
    return <ConfirmationDialog key={key} {...getDialogProps(options)} />;
  }

  return <BasicDialog key={key} {...getDialogProps(options)} />;
}

function DialogManager({ children }: DialogManagerProps) {
  const { addItem, removeItem, mapItems } = useOrderedState<SetDialogOptions>();

  ////////////////////////////////////////////////////////////////
  // API
  ////////////////////////////////////////////////////////////////

  const confirm = useCallback<DialogManagerApi["confirm"]>(
    (options) => {
      const opts = typeof options === "string" ? { content: options } : options;
      const { content, ...rest } = opts;

      return new Promise<boolean>((resolve) => {
        const id = addItem({
          ...rest,
          children: content,
          type: "confirmation",
          onConfirm: () => {
            removeItem(id);
            resolve(true);
          },
          onCancel: () => {
            removeItem(id);
            resolve(false);
          },
        });
      });
    },
    [addItem, removeItem],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <DialogManagerContext.Provider value={{ confirm }}>
      {children}
      {mapItems(getDialog)}
    </DialogManagerContext.Provider>
  );
}

export default DialogManager;
