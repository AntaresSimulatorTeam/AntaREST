import { Button } from "@mui/material";
import { useId, useState } from "react";
import { FieldValues, FormState } from "react-hook-form";
import { useTranslation } from "react-i18next";
import BasicDialog, { BasicDialogProps } from "./BasicDialog";
import Form, { FormProps } from "../Form";

type SuperType<TFieldValues extends FieldValues, TContext> = Omit<
  BasicDialogProps,
  "onSubmit" | "children"
> &
  Omit<FormProps<TFieldValues, TContext>, "hideSubmitButton">;

export interface FormDialogProps<
  TFieldValues extends FieldValues = FieldValues,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  TContext = any
> extends SuperType<TFieldValues, TContext> {
  cancelButtonText?: string;
  onCancel: VoidFunction;
}

// TODO: `formState.isSubmitting` doesn't update when auto submit enabled

function FormDialog<TFieldValues extends FieldValues, TContext>(
  props: FormDialogProps<TFieldValues, TContext>
) {
  const {
    config,
    onSubmit,
    onSubmitError,
    children,
    autoSubmit,
    onStateChange,
    onCancel,
    onClose,
    cancelButtonText,
    submitButtonText,
    ...dialogProps
  } = props;

  const formProps = {
    config,
    onSubmit,
    onSubmitError,
    children,
    autoSubmit,
  };

  const { t } = useTranslation();
  const formId = useId();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitAllowed, setIsSubmitAllowed] = useState(false);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleFormStateChange = (formState: FormState<TFieldValues>) => {
    const { isSubmitting, isDirty } = formState;
    onStateChange?.(formState);
    setIsSubmitting(isSubmitting);
    setIsSubmitAllowed(isDirty && !isSubmitting);
  };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const handleClose: FormDialogProps["onClose"] = (...args) => {
    onCancel();
    onClose?.(...args);
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
            {cancelButtonText || t("button.close")}
          </Button>
          {!autoSubmit && (
            <Button
              type="submit"
              form={formId}
              variant="contained"
              disabled={!isSubmitAllowed}
            >
              {submitButtonText || t("global.save")}
            </Button>
          )}
        </>
      }
    >
      <Form
        {...formProps}
        sx={{
          ".Form__Loader": {
            position: "absolute",
            top: "10px",
            right: "3px",
          },
        }}
        id={formId}
        onStateChange={handleFormStateChange}
        hideSubmitButton
      />
    </BasicDialog>
  );
}

export default FormDialog;
