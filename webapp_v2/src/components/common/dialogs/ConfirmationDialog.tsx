import { Button, ButtonProps } from "@mui/material";
import { useTranslation } from "react-i18next";
import BasicDialog, { BasicDialogProps } from "./BasicDialog";

/**
 * Types
 */

export interface ConfirmationDialogProps
  extends Omit<BasicDialogProps, "actions"> {
  cancelButtonText?: string;
  confirmButtonText?: string;
  cancelButtonProps?: Omit<ButtonProps, "onClick">;
  confirmButtonProps?: Omit<ButtonProps, "onClick">;
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
    cancelButtonProps,
    confirmButtonProps,
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
      onClose={(...args) => {
        onCancel();
        onClose?.(...args);
      }}
      actions={
        <>
          <Button autoFocus {...cancelButtonProps} onClick={onCancel}>
            {cancelButtonText || t("main:noButton")}
          </Button>
          <Button {...confirmButtonProps} onClick={onConfirm}>
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
  cancelButtonProps: null,
  confirmButtonProps: null,
};

export default ConfirmationDialog;
