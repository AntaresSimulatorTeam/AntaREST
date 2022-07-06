import FormDialog, {
  FormDialogProps,
} from "../../../../../common/dialogs/FormDialog";
import TokenForm from "./TokenForm";

/**
 * Types
 */

export interface TokenFormDialogProps
  extends Omit<FormDialogProps, "children"> {
  onlyPermissions?: boolean;
}

/**
 * Component
 */

function TokenFormDialog(props: TokenFormDialogProps) {
  const { onlyPermissions, ...dialogProps } = props;

  return (
    <FormDialog maxWidth="sm" {...dialogProps}>
      {(formObj) => (
        <TokenForm onlyPermissions={onlyPermissions} {...formObj} />
      )}
    </FormDialog>
  );
}

TokenFormDialog.defaultProps = {
  onlyPermissions: false,
};

export default TokenFormDialog;
