import { Button } from "@mui/material";
import { useRef, useState } from "react";
import { FieldValues, FormState } from "react-hook-form";
import { v4 as uuidv4 } from "uuid";
import { useTranslation } from "react-i18next";
import BasicDialog, { BasicDialogProps } from "./BasicDialog";
import Form, { FormProps } from "../Form";

type SuperType<TFieldValues extends FieldValues, TContext> = Omit<
  BasicDialogProps,
  "onSubmit" | "children"
> &
  Omit<FormProps<TFieldValues, TContext>, "disableSubmitButton">;

export interface FormDialogProps<
  TFieldValues extends FieldValues = FieldValues,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  TContext = any
> extends SuperType<TFieldValues, TContext> {
  cancelButtonText?: string;
  onCancel: VoidFunction;
}

function FormDialog<TFieldValues extends FieldValues, TContext>(
  props: FormDialogProps<TFieldValues, TContext>
) {
  const {
    config,
    onSubmit,
    children,
    onCancel,
    onClose,
    cancelButtonText,
    submitButtonText,
    ...dialogProps
  } = props;
  const formId = useRef(uuidv4()).current;
  const formProps = {
    config,
    onSubmit,
    children,
    id: formId,
    disableSubmitButton: true,
  };
  const { t } = useTranslation();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [allowSubmit, setAllowSubmit] = useState(false);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleFormStateChange = ({
    isDirty,
    isValid,
    isSubmitting,
  }: FormState<TFieldValues>) => {
    setIsSubmitting(isSubmitting);
    setAllowSubmit(isDirty && isValid && !isSubmitting);
  };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const handleClose = ((...args) => {
    onCancel();
    onClose?.(...args);
  }) as FormDialogProps["onClose"];

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
          <Button
            type="submit"
            form={formId}
            variant="contained"
            disabled={!allowSubmit}
          >
            {submitButtonText || t("global.save")}
          </Button>
        </>
      }
    >
      <Form
        {...formProps}
        onStateChange={handleFormStateChange}
        hideSubmitButton
      />
    </BasicDialog>
  );
}

export default FormDialog;
