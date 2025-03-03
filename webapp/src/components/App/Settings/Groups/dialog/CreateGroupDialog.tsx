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

import GroupAddIcon from "@mui/icons-material/GroupAdd";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import { usePromise as usePromiseWrapper } from "react-use";
import type {
  GroupDetailsDTO,
  GroupDTO,
  RoleDetailsDTO,
  UserDTO,
} from "../../../../../types/types";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import { createGroup, createRole } from "../../../../../services/api/user";
import type { SubmitHandlerPlus } from "../../../../common/Form/types";
import GroupFormDialog, { type GroupFormDialogProps } from "./GroupFormDialog";

type InheritPropsToOmit = "title" | "titleIcon" | "onSubmit" | "onCancel";

interface Props extends Omit<GroupFormDialogProps, InheritPropsToOmit> {
  addGroup: (group: GroupDetailsDTO) => void;
  reloadFetchGroups: VoidFunction;
  closeDialog: VoidFunction;
}

function CreateGroupDialog(props: Props) {
  const { addGroup, reloadFetchGroups, closeDialog, ...dialogProps } = props;
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const mounted = usePromiseWrapper();
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (data: SubmitHandlerPlus) => {
    const { name, permissions } = data.values;
    let newGroup: GroupDTO;

    try {
      newGroup = await mounted(createGroup(name));
      enqueueSnackbar(t("settings.success.groupCreation", { 0: newGroup.name }), {
        variant: "success",
      });
    } catch (e) {
      enqueueErrorSnackbar(t("settings.error.groupSave", { 0: name }), e as Error);
      throw e;
    }

    try {
      let users: GroupDetailsDTO["users"] = [];

      if (permissions.length > 0) {
        const promises = permissions.map((perm: { user: UserDTO; type: number }) =>
          createRole({
            group_id: newGroup.id,
            type: perm.type,
            identity_id: perm.user.id,
          }),
        );

        const res: RoleDetailsDTO[] = await mounted(Promise.all(promises));

        users = res.map(({ identity, type }) => ({
          id: identity.id,
          name: identity.name,
          role: type,
        }));
      }

      addGroup({ ...newGroup, users });
    } catch (e) {
      // Because we cannot recover roles eventually created
      reloadFetchGroups();

      enqueueErrorSnackbar(t("settings.error.userRolesSave", { 0: newGroup.name }), e as Error);
    }

    closeDialog();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <GroupFormDialog
      title={t("settings.createGroup")}
      titleIcon={GroupAddIcon}
      onSubmit={handleSubmit}
      onCancel={closeDialog}
      {...dialogProps}
    />
  );
}

export default CreateGroupDialog;
