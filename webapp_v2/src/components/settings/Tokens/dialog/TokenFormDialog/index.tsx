import { DialogContentText } from "@mui/material";
import FormDialog, {
  FormDialogProps,
} from "../../../../common/dialogs/FormDialog";
import TokenForm from "./TokenForm";

/**
 * Types
 */

export interface TokenFormDialogProps
  extends Omit<FormDialogProps, "children"> {
  onlyPermissions?: boolean;
  subtitle?: string;
}

/**
 * Component
 */

function TokenFormDialog(props: TokenFormDialogProps) {
  const { onlyPermissions, subtitle, ...dialogProps } = props;

  return (
    <FormDialog
      maxWidth="sm"
      formOptions={{ mode: "onTouched" }}
      {...dialogProps}
    >
      {(formObj) => (
        <>
          {subtitle && <DialogContentText>{subtitle}</DialogContentText>}
          <TokenForm onlyPermissions={onlyPermissions} {...formObj} />
        </>
      )}
    </FormDialog>
  );
}

TokenFormDialog.defaultProps = {
  onlyPermissions: false,
  subtitle: "",
};

export default TokenFormDialog;
