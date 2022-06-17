import GroupAddIcon from "@mui/icons-material/GroupAdd";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import { usePromise as usePromiseWrapper } from "react-use";
import {
  GroupDetailsDTO,
  GroupDTO,
  RoleDetailsDTO,
  UserDTO,
} from "../../../../common/types";
import useEnqueueErrorSnackbar from "../../../../hooks/useEnqueueErrorSnackbar";
import { createGroup, createRole } from "../../../../services/api/user";
import { SubmitHandlerData } from "../../../common/Form";
import GroupFormDialog, { GroupFormDialogProps } from "./GroupFormDialog";

/**
 * Types
 */

type InheritPropsToOmit = "title" | "titleIcon" | "onSubmit" | "onCancel";

interface Props extends Omit<GroupFormDialogProps, InheritPropsToOmit> {
  addGroup: (group: GroupDetailsDTO) => void;
  reloadFetchGroups: VoidFunction;
  closeDialog: VoidFunction;
}

/**
 * Component
 */

function CreateGroupDialog(props: Props) {
  const { addGroup, reloadFetchGroups, closeDialog, ...dialogProps } = props;
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const mounted = usePromiseWrapper();
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (data: SubmitHandlerData) => {
    const { name, permissions } = data.values;
    let newGroup: GroupDTO;

    try {
      newGroup = await mounted(createGroup(name));
      enqueueSnackbar(t("settings.success.groupCreation", [newGroup.name]), {
        variant: "success",
      });
    } catch (e) {
      enqueueErrorSnackbar(t("settings.error.groupSave", [name]), e as Error);
      throw e;
    }

    try {
      let users: GroupDetailsDTO["users"] = [];

      if (permissions.length > 0) {
        const promises = permissions.map(
          (perm: { user: UserDTO; type: number }) =>
            createRole({
              group_id: newGroup.id,
              type: perm.type,
              identity_id: perm.user.id,
            })
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

      enqueueErrorSnackbar(
        t("settings.error.userRolesSave", [newGroup.name]),
        e as Error
      );
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
