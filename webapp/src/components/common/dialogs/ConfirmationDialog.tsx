/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { useTranslation } from "react-i18next";

import { Button } from "@mui/material";

import BasicDialog, { BasicDialogProps } from "./BasicDialog";

export interface ConfirmationDialogProps
  extends Omit<BasicDialogProps, "actions"> {
  cancelButtonText?: string;
  confirmButtonText?: string;
  onConfirm: VoidFunction;
  onCancel: VoidFunction;
}

function ConfirmationDialog(props: ConfirmationDialogProps) {
  const {
    cancelButtonText,
    confirmButtonText,
    onConfirm,
    onCancel,
    onClose,
    ...basicDialogProps
  } = props;

  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleClose = (
    ...args: Parameters<NonNullable<BasicDialogProps["onClose"]>>
  ) => {
    onCancel();
    onClose?.(...args);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <BasicDialog
      title={t("dialog.title.confirmation")}
      onClose={handleClose}
      {...basicDialogProps}
      actions={
        <>
          <Button onClick={onCancel}>
            {cancelButtonText || t("button.no")}
          </Button>
          <Button onClick={onConfirm} variant="contained">
            {confirmButtonText || t("button.yes")}
          </Button>
        </>
      }
    />
  );
}

export default ConfirmationDialog;
