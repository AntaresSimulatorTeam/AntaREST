import { Button } from "@mui/material";
import { useTranslation } from "react-i18next";
import BasicDialog, { BasicDialogProps } from "./BasicDialog";

/**
 * Types
 */

export interface ConfirmationDialogProps
  extends Omit<BasicDialogProps, "actions"> {
  cancelButtonText?: string;
  confirmButtonText?: string;
  onConfirm: VoidFunction;
  onCancel: VoidFunction;
}

/**
 * Component
 */

function ConfirmationDialog(props: ConfirmationDialogProps) {
  const {
    cancelButtonText,
    confirmButtonText,
    onConfirm,
    onCancel,
    onClose,
    ...basicDialogProps
  } = props;

  const { t } = useTranslation();

  return (
    <BasicDialog
      title={t("dialog.title.confirmation")}
      {...basicDialogProps}
      actions={
        <>
          <Button onClick={onCancel}>
            {cancelButtonText || t("button.no")}
          </Button>
          <Button onClick={onConfirm} variant="contained">
            {confirmButtonText || t("button.yes")}
          </Button>
        </>
      }
    />
  );
}

ConfirmationDialog.defaultProps = {
  cancelButtonText: null,
  confirmButtonText: null,
};

export default ConfirmationDialog;
