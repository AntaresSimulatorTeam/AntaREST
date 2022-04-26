import { Backdrop, Box, CircularProgress } from "@mui/material";
import { ReactNode } from "react";
import { FieldValues, UnpackNestedValue, useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { L, F } from "ts-toolbelt";
import * as R from "ramda";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import ConfirmationDialog, {
  ConfirmationDialogProps,
} from "./ConfirmationDialog";

/**
 * Types
 */

export type SubmitHandlerData<TFieldValues extends FieldValues = FieldValues> =
  {
    values: UnpackNestedValue<TFieldValues>;
    modifiedValues: UnpackNestedValue<TFieldValues>;
  };

export type FormObj = Omit<ReturnType<typeof useForm>, "handleSubmit">;

export interface FormDialogProps
  extends Omit<ConfirmationDialogProps, "onConfirm" | "onSubmit"> {
  formOptions?: L.Head<Parameters<typeof useForm>>;
  onSubmit: <TFieldValues extends FieldValues>(
    data: SubmitHandlerData<TFieldValues>,
    event?: React.BaseSyntheticEvent
  ) => unknown | Promise<unknown>;
  children: (formObj: FormObj) => ReactNode;
}

/**
 * Component
 */

function FormDialog(props: FormDialogProps) {
  const { onCancel, onClose, formOptions, onSubmit, children, ...dialogProps } =
    props;
  const { handleSubmit, ...formObj } = useForm(formOptions);
  const { t } = useTranslation();
  const {
    formState: { isValid, isSubmitting, isDirty, dirtyFields },
  } = formObj;
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const invokeIfNotSubmitting = <T extends unknown[]>(fn?: F.Function<T>) => {
    return (...args: T) => {
      if (!isSubmitting) {
        fn?.(...args);
      }
    };
  };

  const handleConfirm = () => {
    handleSubmit((data, event) => {
      const dirtyValues = R.pickBy(
        (val, key) => dirtyFields[key],
        data
      ) as object;

      return onSubmit({ values: data, modifiedValues: dirtyValues }, event);
    })().catch((error) => {
      enqueueErrorSnackbar(t("main:form.submit.error"), error);
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ConfirmationDialog
      maxWidth="xs"
      fullWidth
      cancelButtonText={t("main:closeButton")}
      confirmButtonText={t("main:save")}
      {...dialogProps}
      onConfirm={handleConfirm}
      cancelButtonProps={{
        ...dialogProps.cancelButtonProps,
        disabled: isSubmitting,
      }}
      confirmButtonProps={{
        ...dialogProps.confirmButtonProps,
        disabled: !isDirty || !isValid || isSubmitting,
      }}
      onCancel={invokeIfNotSubmitting(onCancel)}
      onClose={invokeIfNotSubmitting(onClose)}
    >
      <Box>
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
