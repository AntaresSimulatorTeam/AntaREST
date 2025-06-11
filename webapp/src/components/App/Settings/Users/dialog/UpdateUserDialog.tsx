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
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { usePromise as usePromiseWrapper } from "react-use";
import type { UserEdit } from "..";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import { createRole, deleteUserRoles } from "../../../../../services/api/user";
import type { GroupDTO, RoleType, UserDetailsDTO } from "../../../../../types/types";
import type { SubmitHandlerPlus } from "../../../../common/Form/types";
import UserFormDialog from "./UserFormDialog";
import type { UserFormDefaultValues } from "./utils";

interface Props {
  open: boolean;
  user: UserDetailsDTO;
  editUser: (user: UserEdit) => void;
  reloadFetchUsers: VoidFunction;
  onCancel: VoidFunction;
}

function UpdateUserDialog({ open, user, onCancel, editUser, reloadFetchUsers }: Props) {
  const { t } = useTranslation();
  const mounted = usePromiseWrapper();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const defaultPermissions = useMemo<UserFormDefaultValues["permissions"]>(
    () =>
      user.roles.map((role) => ({
        group: {
          id: role.group_id,
          name: role.group_name,
        },
        type: role.type,
      })),
    [user],
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (data: SubmitHandlerPlus) => {
    const { permissions } = data.values;

    // TODO: replace with update method when working

    try {
      await mounted(deleteUserRoles(user.id));

      const promises = permissions.map((perm: { group: GroupDTO; type: RoleType }) =>
        createRole({
          group_id: perm.group.id,
          type: perm.type,
          identity_id: user.id,
        }),
      );

      const res = await mounted(Promise.all(promises));

      const roles = res.map(({ group, identity, type }) => ({
        group_id: group.id,
        group_name: group.name,
        identity_id: identity.id,
        type,
      }));

      editUser({ id: user.id, roles });

      enqueueSnackbar(t("settings.success.userUpdate", { 0: user.name }), {
        variant: "success",
      });
    } catch (e) {
      // Because we cannot recover roles eventually deleted/created
      reloadFetchUsers();

      enqueueErrorSnackbar(t("settings.error.userRolesSave", { 0: user.name }), e as Error);
    }

    onCancel();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UserFormDialog
      open={open}
      title={t("settings.updateUser")}
      titleIcon={EditIcon}
      defaultValues={{ username: user.name, permissions: defaultPermissions }}
      onSubmit={handleSubmit}
      onCancel={onCancel}
      onlyPermissions
    />
  );
}

export default UpdateUserDialog;
