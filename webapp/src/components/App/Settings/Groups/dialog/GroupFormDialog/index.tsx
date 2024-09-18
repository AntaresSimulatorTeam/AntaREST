/** Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import FormDialog, {
  FormDialogProps,
} from "../../../../../common/dialogs/FormDialog";
import { RoleType, UserDTO } from "../../../../../../common/types";
import GroupForm from "./GroupForm";

/**
 * Types
 */

export interface GroupFormDialogProps
  extends Omit<FormDialogProps, "children"> {
  defaultValues?: {
    name?: string;
    permissions?: Array<{ user: UserDTO; type: RoleType }>;
  };
}

/**
 * Component
 */

function GroupFormDialog(props: GroupFormDialogProps) {
  const { defaultValues, ...dialogProps } = props;

  return (
    <FormDialog maxWidth="sm" config={{ defaultValues }} {...dialogProps}>
      {GroupForm}
    </FormDialog>
  );
}

GroupFormDialog.defaultProps = {
  defaultValues: undefined,
};

export default GroupFormDialog;
