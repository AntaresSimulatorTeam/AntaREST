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

import FormDialog, { type FormDialogProps } from "../../../../../common/dialogs/FormDialog";
import TokenForm from "./TokenForm";

export interface TokenFormDialogProps extends Omit<FormDialogProps, "children"> {
  onlyPermissions?: boolean;
}

function TokenFormDialog(props: TokenFormDialogProps) {
  const { onlyPermissions, ...dialogProps } = props;

  return (
    <FormDialog maxWidth="sm" {...dialogProps}>
      {(formObj) => <TokenForm onlyPermissions={onlyPermissions} {...formObj} />}
    </FormDialog>
  );
}

export default TokenFormDialog;
