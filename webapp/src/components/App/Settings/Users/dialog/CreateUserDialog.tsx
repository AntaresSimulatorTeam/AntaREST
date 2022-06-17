import PersonAddIcon from "@mui/icons-material/PersonAdd";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import { usePromise as usePromiseWrapper } from "react-use";
import {
  GroupDTO,
  RoleDetailsDTO,
  RoleType,
  UserDetailsDTO,
  UserDTO,
} from "../../../../../common/types";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import { createRole, createUser } from "../../../../../services/api/user";
import { SubmitHandlerData } from "../../../../common/Form";
import UserFormDialog, { UserFormDialogProps } from "./UserFormDialog";

type InheritPropsToOmit = "title" | "titleIcon" | "onSubmit" | "onCancel";

interface Props extends Omit<UserFormDialogProps, InheritPropsToOmit> {
  addUser: (user: UserDetailsDTO) => void;
  reloadFetchUsers: VoidFunction;
  closeDialog: VoidFunction;
}

function CreateUserDialog(props: Props) {
  const { addUser, reloadFetchUsers, closeDialog, ...dialogProps } = props;
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const mounted = usePromiseWrapper();
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (data: SubmitHandlerData) => {
    const { username, password, permissions } = data.values;
    let newUser: UserDTO;

    try {
      newUser = await mounted(createUser(username, password));
      enqueueSnackbar(t("settings.success.userCreation", [newUser.name]), {
        variant: "success",
      });
    } catch (e) {
      enqueueErrorSnackbar(
        t("settings.error.userSave", [username]),
        e as Error
      );
      throw e;
    }

    try {
      let roles: UserDetailsDTO["roles"] = [];

      if (permissions.length > 0) {
        const promises = permissions.map(
          (perm: { group: GroupDTO; type: RoleType }) =>
            createRole({
              group_id: perm.group.id,
              type: perm.type,
              identity_id: newUser.id,
            })
        );

        const res: RoleDetailsDTO[] = await mounted(Promise.all(promises));

        roles = res.map(({ group, identity, type }) => ({
          group_id: group.id,
          group_name: group.name,
          identity_id: identity.id,
          type,
        }));
      }

      addUser({ ...newUser, roles });
    } catch (e) {
      // Because we cannot recover roles eventually created
      reloadFetchUsers();

      enqueueErrorSnackbar(
        t("settings.error.userRolesSave", [newUser.name]),
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
      title={t("settings.createUser")}
      titleIcon={PersonAddIcon}
      onSubmit={handleSubmit}
      onCancel={closeDialog}
      {...dialogProps}
    />
  );
}

export default CreateUserDialog;
