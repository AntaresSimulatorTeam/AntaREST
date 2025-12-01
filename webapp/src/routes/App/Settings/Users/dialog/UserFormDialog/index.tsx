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

import FormDialog, { type FormDialogProps } from "../../../../../common/dialogs/FormDialog";
import { USER_FORM_DEFAULT_VALUES, type UserFormDefaultValues } from "../utils";
import UserForm from "./UserForm";

export interface UserFormDialogProps
  extends Omit<FormDialogProps<UserFormDefaultValues>, "children" | "maxWidth"> {
  defaultValues?: Partial<UserFormDefaultValues>;
  onlyPermissions?: boolean;
}

function UserFormDialog({
  defaultValues: defaultValuesFromProps,
  onlyPermissions,
  ...dialogProps
}: UserFormDialogProps) {
  return (
    <FormDialog
      maxWidth="xs"
      config={{ defaultValues: { ...USER_FORM_DEFAULT_VALUES, ...defaultValuesFromProps } }}
      {...dialogProps}
    >
      <UserForm onlyPermissions={onlyPermissions} />
    </FormDialog>
  );
}

export default UserFormDialog;
