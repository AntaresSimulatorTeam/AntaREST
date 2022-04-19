import { Button } from "@mui/material";
import { MouseEventHandler, PropsWithChildren } from "react";
import { useTranslation } from "react-i18next";
import BasicDialog, { BasicDialogProps } from "./BasicDialog";

/**
 * Types
 */

interface Props extends Omit<BasicDialogProps, "actions"> {
  cancelButtonText?: string;
  confirmButtonText?: string;
  onConfirm: MouseEventHandler<HTMLButtonElement>;
  onCancel: MouseEventHandler<HTMLButtonElement>;
}

/**
 * Component
 */

function ConfirmDialog(props: PropsWithChildren<Props>) {
  const {
    cancelButtonText,
    confirmButtonText,
    onConfirm,
    onCancel,
    ...basicDialogProps
  } = props;

  const { t } = useTranslation();

  return (
    <BasicDialog
      onClose={onCancel}
      onBackdropClick={onCancel}
      {...basicDialogProps}
      actions={
        <>
          <Button onClick={onCancel} autoFocus>
            {cancelButtonText || t("main:noButton")}
          </Button>
          <Button onClick={onConfirm}>
            {confirmButtonText || t("main:yesButton")}
          </Button>
        </>
      }
    />
  );
}

ConfirmDialog.defaultProps = {
  cancelButtonText: null,
  confirmButtonText: null,
};

export default ConfirmDialog;
