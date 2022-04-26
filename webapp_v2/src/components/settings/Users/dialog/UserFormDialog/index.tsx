import { Box, DialogContentText, Typography } from "@mui/material";
import FormDialog, {
  FormDialogProps,
} from "../../../../common/dialogs/FormDialog";
import { GroupDTO, RoleType } from "../../../../../common/types";
import UserForm from "./UserForm";

/**
 * Types
 */

export interface UserFormDialogProps {
  open: FormDialogProps["open"];
  onSubmit: FormDialogProps["onSubmit"];
  onCancel: FormDialogProps["onCancel"];
  title: FormDialogProps["title"];
  titleIcon: FormDialogProps["titleIcon"];
  defaultValues?: {
    username?: string;
    password?: string;
    permissions?: Array<{ group: GroupDTO; type: RoleType }>;
  };
  onlyPermissions?: boolean;
  subtitle?: string;
}

/**
 * Component
 */

function UserFormDialog(props: UserFormDialogProps) {
  const { defaultValues, onlyPermissions, subtitle, ...dialogProps } = props;

  return (
    <FormDialog
      maxWidth="sm"
      formOptions={{ mode: "onTouched", defaultValues }}
      {...dialogProps}
    >
      {(formObj) => (
        <>
          {subtitle && <DialogContentText>{subtitle}</DialogContentText>}
          <UserForm onlyPermissions={onlyPermissions} {...formObj} />
        </>
      )}
    </FormDialog>
  );
}

UserFormDialog.defaultProps = {
  defaultValues: undefined,
  onlyPermissions: false,
  subtitle: "",
};

export default UserFormDialog;
