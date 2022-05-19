import { Backdrop, Box, Button, CircularProgress } from "@mui/material";
import { FormEvent, ReactNode, useRef } from "react";
import {
  FieldValues,
  UnpackNestedValue,
  useForm,
  UseFormProps,
  UseFormReturn,
} from "react-hook-form";
import { useTranslation } from "react-i18next";
import * as R from "ramda";
import { v4 as uuidv4 } from "uuid";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import BasicDialog, { BasicDialogProps } from "./BasicDialog";

/**
 * Types
 */

export type SubmitHandlerData<TFieldValues extends FieldValues = FieldValues> =
  {
    values: UnpackNestedValue<TFieldValues>;
    modifiedValues: UnpackNestedValue<TFieldValues>;
  };

export interface FormObj extends Omit<UseFormReturn, "handleSubmit"> {
  defaultValues: UseFormProps["defaultValues"];
}

export interface FormDialogProps extends Omit<BasicDialogProps, "onSubmit"> {
  formOptions?: UseFormProps;
  cancelButtonText?: string;
  submitButtonText?: string;
  onSubmit: <TFieldValues extends FieldValues>(
    data: SubmitHandlerData<TFieldValues>,
    event?: React.BaseSyntheticEvent
  ) => unknown | Promise<unknown>;
  onCancel: VoidFunction;
  children: (formObj: FormObj) => ReactNode;
}

/**
 * Component
 */

function FormDialog(props: FormDialogProps) {
  const {
    onCancel,
    onClose,
    formOptions,
    onSubmit,
    cancelButtonText,
    submitButtonText,
    children,
    ...dialogProps
  } = props;
  const { handleSubmit, ...formObj } = useForm({
    mode: "onChange",
    ...formOptions,
  });
  const { t } = useTranslation();
  const formId = useRef(uuidv4()).current;
  const {
    formState: { isValid, isSubmitting, isDirty, dirtyFields },
  } = formObj;
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const allowSubmit = isDirty && isValid && !isSubmitting;

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const handleClose = ((...args) => {
    onCancel();
    onClose?.(...args);
  }) as FormDialogProps["onClose"];

  const handleFormSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    handleSubmit((data, event) => {
      const dirtyValues = R.pickBy(
        (val, key) => dirtyFields[key],
        data
      ) as FieldValues;

      return onSubmit({ values: data, modifiedValues: dirtyValues }, event);
    })().catch((error) => {
      enqueueErrorSnackbar(t("main:form.submit.error"), error);
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <BasicDialog
      maxWidth="xs"
      fullWidth
      {...dialogProps}
      onClose={handleClose}
      actions={
        <>
          <Button onClick={onCancel} disabled={isSubmitting}>
            {cancelButtonText || t("global:button.close")}
          </Button>
          <Button
            type="submit"
            form={formId}
            variant="contained"
            disabled={!allowSubmit}
          >
            {submitButtonText || t("global:global.save")}
          </Button>
        </>
      }
    >
      <Box>
        <form id={formId} onSubmit={handleFormSubmit}>
          {children({ defaultValues: formOptions?.defaultValues, ...formObj })}
        </form>
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
    </BasicDialog>
  );
}

FormDialog.defaultProps = {
  formOptions: null,
  cancelButtonText: null,
  submitButtonText: null,
};

export default FormDialog;
