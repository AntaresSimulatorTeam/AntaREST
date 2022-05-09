import FormDialog, {
  FormDialogProps,
} from "../../../../common/dialogs/FormDialog";
import { RoleType, UserDTO } from "../../../../../common/types";
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
    <FormDialog maxWidth="sm" formOptions={{ defaultValues }} {...dialogProps}>
      {GroupForm}
    </FormDialog>
  );
}

GroupFormDialog.defaultProps = {
  defaultValues: undefined,
};

export default GroupFormDialog;
