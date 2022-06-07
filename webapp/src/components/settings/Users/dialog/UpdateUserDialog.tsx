import EditIcon from "@mui/icons-material/Edit";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { usePromise as usePromiseWrapper } from "react-use";
import { useSnackbar } from "notistack";
import { GroupDTO, RoleType, UserDetailsDTO } from "../../../../common/types";
import { createRole, deleteUserRoles } from "../../../../services/api/user";
import UserFormDialog, { UserFormDialogProps } from "./UserFormDialog";
import { UserEdit } from "..";
import useEnqueueErrorSnackbar from "../../../../hooks/useEnqueueErrorSnackbar";
import { SubmitHandlerData } from "../../../common/Form";

type InheritPropsToOmit =
  | "title"
  | "titleIcon"
  | "defaultValues"
  | "onSubmit"
  | "onCancel";

interface Props extends Omit<UserFormDialogProps, InheritPropsToOmit> {
  user: UserDetailsDTO;
  closeDialog: VoidFunction;
  editUser: (user: UserEdit) => void;
  reloadFetchUsers: VoidFunction;
}

function UpdateUserDialog(props: Props) {
  const { user, closeDialog, editUser, reloadFetchUsers, ...dialogProps } =
    props;
  const { t } = useTranslation();
  const mounted = usePromiseWrapper();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const defaultValues = useMemo(
    () => ({
      permissions: user.roles.map((role) => ({
        group: {
          id: role.group_id,
          name: role.group_name,
        },
        type: role.type,
      })),
    }),
    [user]
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (data: SubmitHandlerData) => {
    const { permissions } = data.values;

    // TODO: replace with update method when working

    try {
      await mounted(deleteUserRoles(user.id));

      const promises = permissions.map(
        (perm: { group: GroupDTO; type: RoleType }) =>
          createRole({
            group_id: perm.group.id,
            type: perm.type,
            identity_id: user.id,
          })
      );

      const res = await mounted(Promise.all(promises));

      const roles = res.map(({ group, identity, type }) => ({
        group_id: group.id,
        group_name: group.name,
        identity_id: identity.id,
        type,
      }));

      editUser({ id: user.id, roles });

      enqueueSnackbar(t("settings.success.userUpdate", [user.name]), {
        variant: "success",
      });
    } catch (e) {
      // Because we cannot recover roles eventually deleted/created
      reloadFetchUsers();

      enqueueErrorSnackbar(
        t("settings.error.userRolesSave", [user.name]),
        e as Error
      );
    }

    closeDialog();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UserFormDialog
      title={t("settings.updateUser")}
      subtitle={t("settings.currentUser", [user.name])}
      titleIcon={EditIcon}
      defaultValues={defaultValues}
      onSubmit={handleSubmit}
      onCancel={closeDialog}
      onlyPermissions
      {...dialogProps}
    />
  );
}

export default UpdateUserDialog;
