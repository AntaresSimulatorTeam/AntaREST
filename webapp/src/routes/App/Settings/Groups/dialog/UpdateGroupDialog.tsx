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

import EditIcon from "@mui/icons-material/Edit";
import { useSnackbar } from "notistack";
import * as R from "ramda";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { usePromise as usePromiseWrapper } from "react-use";
import type { GroupEdit } from "..";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import {
  createRole,
  deleteUserRole,
  getRolesForGroup,
  updateGroup,
} from "../../../../../services/api/user";
import type { GroupDetailsDTO } from "../../../../../types/types";
import type { SubmitHandlerPlus } from "../../../../common/Form/types";
import GroupFormDialog from "./GroupFormDialog";
import type { GroupFormDefaultValues } from "./utils";

interface Props {
  open: boolean;
  group: GroupDetailsDTO;
  editGroup: (user: GroupEdit) => void;
  reloadFetchGroups: VoidFunction;
  onCancel: VoidFunction;
}

function UpdateGroupDialog({
  open,
  group,
  onCancel,
  editGroup,
  reloadFetchGroups: reloadFetchUsers,
}: Props) {
  const { t } = useTranslation();
  const mounted = usePromiseWrapper();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const defaultValues = useMemo<GroupFormDefaultValues>(
    () => ({
      name: group.name,
      permissions: group.users.map((user) => ({
        user: {
          id: user.id,
          name: user.name,
        },
        type: user.role,
      })),
    }),
    [group],
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async ({
    dirtyValues,
    values,
  }: SubmitHandlerPlus<GroupFormDefaultValues>) => {
    const groupName = dirtyValues.name || group.name;

    const notifySuccess = R.once(() =>
      enqueueSnackbar(t("settings.success.groupUpdate", { 0: groupName }), {
        variant: "success",
      }),
    );

    if (groupName !== group.name) {
      try {
        await mounted(updateGroup(group.id, groupName));
        editGroup({ id: group.id, name: groupName });
        notifySuccess();
      } catch (e) {
        enqueueErrorSnackbar(t("settings.error.groupSave", { 0: groupName }), e as Error);
        throw e;
      }
    }

    if (dirtyValues.permissions) {
      const { permissions } = values;

      try {
        const userRolesToDelete = group.users.filter((userRole) => {
          return !permissions.some((perm) => perm.user.id === userRole.id);
        });

        const permsToUpdate = permissions.filter((perm) => {
          const userRole = group.users.find((role) => perm.user.id === role.id);
          return userRole ? userRole.role !== perm.type : false;
        });

        const permsToCreate = permissions.filter((perm) => {
          return !group.users.some((userRole) => userRole.id === perm.user.id);
        });

        const promises = [
          ...userRolesToDelete.map((role) => deleteUserRole(role.id, group.id)),
          ...permsToUpdate.map(async (perm) => {
            // TODO: replace with update method when working
            await deleteUserRole(perm.user.id, group.id);
            await createRole({
              identity_id: perm.user.id,
              type: perm.type,
              group_id: group.id,
            });
          }),
          ...permsToCreate.map((role) =>
            createRole({
              identity_id: role.user.id,
              type: role.type,
              group_id: group.id,
            }),
          ),
        ];

        await mounted(Promise.all(promises));

        const newUserRoles = (await mounted(getRolesForGroup(group.id))).map(
          ({ identity, type }) => ({
            id: identity.id,
            name: identity.name,
            role: type,
          }),
        );

        editGroup({ id: group.id, name: groupName, users: newUserRoles });

        notifySuccess();
      } catch (e) {
        // Because we cannot recover roles eventually deleted/created
        reloadFetchUsers();

        enqueueErrorSnackbar(t("settings.error.groupRolesSave", { 0: groupName }), e as Error);
      }
    }

    onCancel();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <GroupFormDialog
      open={open}
      title={t("settings.updateGroup")}
      titleIcon={EditIcon}
      defaultValues={defaultValues}
      onSubmit={handleSubmit}
      onCancel={onCancel}
    />
  );
}

export default UpdateGroupDialog;
