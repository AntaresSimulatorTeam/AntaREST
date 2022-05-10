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
      title={t("main:confirmationModalTitle")}
      {...basicDialogProps}
      actions={
        <>
          <Button onClick={onCancel}>
            {cancelButtonText || t("main:noButton")}
          </Button>
          <Button onClick={onConfirm} variant="contained">
            {confirmButtonText || t("main:yesButton")}
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
