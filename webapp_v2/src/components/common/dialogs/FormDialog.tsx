import { Backdrop, Box, CircularProgress } from "@mui/material";
import { ReactNode } from "react";
import { FieldValues, SubmitHandler, useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { L } from "ts-toolbelt";
import ConfirmationDialog, {
  ConfirmationDialogProps,
} from "./ConfirmationDialog";

/**
 * Types
 */

export type FormObj = Omit<ReturnType<typeof useForm>, "handleSubmit">;

export interface FormDialogProps
  extends Omit<ConfirmationDialogProps, "onConfirm"> {
  formOptions?: L.Head<Parameters<typeof useForm>>;
  onSubmit: SubmitHandler<FieldValues>;
  children: (formObj: FormObj) => ReactNode;
}

/**
 * Component
 */

function FormDialog(props: FormDialogProps) {
  const { formOptions, onSubmit, children, ...dialogProps } = props;
  const { handleSubmit, ...formObj } = useForm(formOptions);
  const { t } = useTranslation();
  const {
    formState: { isValid, isSubmitting },
  } = formObj;

  return (
    <ConfirmationDialog
      maxWidth="xs"
      fullWidth
      cancelButtonText={t("main:closeButton")}
      confirmButtonText={t("main:save")}
      {...dialogProps}
      onConfirm={handleSubmit(onSubmit)}
      cancelButtonProps={{
        ...dialogProps.cancelButtonProps,
        disabled: isSubmitting,
      }}
      confirmButtonProps={{
        ...dialogProps.confirmButtonProps,
        disabled: !isValid || isSubmitting,
      }}
      onClose={(...args) => {
        if (!isSubmitting) {
          dialogProps.onClose?.(...args);
        }
      }}
    >
      <Box sx={{ position: "relative" }}>
        {children(formObj)}
        <Backdrop
          open={isSubmitting}
          sx={{
            position: "absolute",
            zIndex: (theme) => theme.zIndex.drawer + 1,
          }}
        >
          <CircularProgress color="inherit" />
        </Backdrop>
      </Box>
    </ConfirmationDialog>
  );
}

FormDialog.defaultProps = {
  formOptions: null,
};

export default FormDialog;
