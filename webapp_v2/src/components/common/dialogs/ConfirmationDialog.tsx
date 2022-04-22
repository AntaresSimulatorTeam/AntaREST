import { Button, ButtonProps } from "@mui/material";
import { MouseEventHandler } from "react";
import { useTranslation } from "react-i18next";
import * as RA from "ramda-adjunct";
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
  onConfirm: MouseEventHandler<HTMLButtonElement>;
  onCancel: MouseEventHandler<HTMLButtonElement>;
}

/**
 * Component
 */

function ConfirmationDialog(props: ConfirmationDialogProps) {
  const {
    title,
    cancelButtonText,
    confirmButtonText,
    cancelButtonProps,
    confirmButtonProps,
    onConfirm,
    onCancel,
    ...basicDialogProps
  } = props;

  const { t } = useTranslation();

  return (
    <BasicDialog
      title={RA.isUndefined(title) ? t("main:confirmationModalTitle") : title}
      onClose={onCancel}
      onBackdropClick={onCancel}
      noCloseIcon
      {...basicDialogProps}
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
