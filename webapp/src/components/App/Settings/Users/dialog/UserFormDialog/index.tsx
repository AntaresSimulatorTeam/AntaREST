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

import { DialogContentText } from "@mui/material";
import FormDialog, { type FormDialogProps } from "../../../../../common/dialogs/FormDialog";
import type { GroupDTO, RoleType } from "../../../../../../types/types";
import UserForm from "./UserForm";

export interface UserFormDialogProps extends Omit<FormDialogProps, "children"> {
  defaultValues?: {
    username?: string;
    password?: string;
    permissions?: Array<{ group: GroupDTO; type: RoleType }>;
  };
  onlyPermissions?: boolean;
  subtitle?: string;
}

function UserFormDialog(props: UserFormDialogProps) {
  const { defaultValues, onlyPermissions, subtitle, ...dialogProps } = props;

  return (
    <FormDialog maxWidth="sm" config={{ defaultValues }} {...dialogProps}>
      {(formObj) => (
        <>
          {subtitle && <DialogContentText>{subtitle}</DialogContentText>}
          <UserForm onlyPermissions={onlyPermissions} {...formObj} />
        </>
      )}
    </FormDialog>
  );
}

export default UserFormDialog;
