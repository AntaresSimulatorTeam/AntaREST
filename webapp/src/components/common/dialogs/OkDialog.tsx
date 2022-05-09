import { Button, ButtonProps } from "@mui/material";
import { useTranslation } from "react-i18next";
import BasicDialog, { BasicDialogProps } from "./BasicDialog";

/**
 * Types
 */

export interface OkDialogProps extends Omit<BasicDialogProps, "actions"> {
  okButtonText?: string;
  okButtonProps?: Omit<ButtonProps, "onClick">;
  onOk: VoidFunction;
}

/**
 * Component
 */

function OkDialog(props: OkDialogProps) {
  const { okButtonText, okButtonProps, onOk, onClose, ...basicDialogProps } =
    props;
  const { t } = useTranslation();

  return (
    <BasicDialog
      onClose={(...args) => {
        onOk();
        onClose?.(...args);
      }}
      {...basicDialogProps}
      actions={
        <Button autoFocus variant="contained" {...okButtonProps} onClick={onOk}>
          {okButtonText || t("main:okButton")}
        </Button>
      }
    />
  );
}

OkDialog.defaultProps = {
  okButtonText: null,
  okButtonProps: null,
};

export default OkDialog;
