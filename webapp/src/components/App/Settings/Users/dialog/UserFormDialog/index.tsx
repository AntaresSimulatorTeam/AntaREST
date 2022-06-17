import { DialogContentText } from "@mui/material";
import FormDialog, {
  FormDialogProps,
} from "../../../../../common/dialogs/FormDialog";
import { GroupDTO, RoleType } from "../../../../../../common/types";
import UserForm from "./UserForm";

/**
 * Types
 */

export interface UserFormDialogProps extends Omit<FormDialogProps, "children"> {
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

UserFormDialog.defaultProps = {
  defaultValues: undefined,
  onlyPermissions: false,
  subtitle: "",
};

export default UserFormDialog;
