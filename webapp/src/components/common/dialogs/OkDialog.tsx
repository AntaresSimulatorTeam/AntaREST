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

import { Button, type ButtonProps } from "@mui/material";
import { useTranslation } from "react-i18next";
import BasicDialog, { type BasicDialogProps } from "./BasicDialog";

export interface OkDialogProps extends Omit<BasicDialogProps, "actions"> {
  okButtonText?: string;
  okButtonProps?: Omit<ButtonProps, "onClick">;
  onOk: VoidFunction;
}

function OkDialog(props: OkDialogProps) {
  const { okButtonText, okButtonProps, onOk, onClose, ...basicDialogProps } = props;
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleClose = (...args: Parameters<NonNullable<BasicDialogProps["onClose"]>>) => {
    onOk();
    onClose?.(...args);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <BasicDialog
      onClose={handleClose}
      {...basicDialogProps}
      actions={
        <Button autoFocus variant="contained" {...okButtonProps} onClick={onOk}>
          {okButtonText || t("button.ok")}
        </Button>
      }
    />
  );
}

export default OkDialog;
