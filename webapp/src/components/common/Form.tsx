import { FormEvent } from "react";
import {
  FieldValues,
  FormState,
  UnpackNestedValue,
  useForm,
  UseFormProps,
  UseFormReturn,
} from "react-hook-form";
import { useTranslation } from "react-i18next";
import * as R from "ramda";
import { Button } from "@mui/material";
import { useUpdateEffect } from "react-use";
import useEnqueueErrorSnackbar from "../../hooks/useEnqueueErrorSnackbar";
import BackdropLoading from "./loaders/BackdropLoading";

export interface SubmitHandlerData<
  TFieldValues extends FieldValues = FieldValues
> {
  values: UnpackNestedValue<TFieldValues>;
  modifiedValues: Partial<UnpackNestedValue<TFieldValues>>;
}

export interface FormObj<
  TFieldValues extends FieldValues = FieldValues,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  TContext = any
> extends Omit<UseFormReturn<TFieldValues, TContext>, "handleSubmit"> {
  defaultValues: UseFormProps<TFieldValues, TContext>["defaultValues"];
}

export interface FormProps<
  TFieldValues extends FieldValues = FieldValues,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  TContext = any
> {
  formOptions?: UseFormProps<TFieldValues, TContext>;
  onSubmit: (
    data: SubmitHandlerData<TFieldValues>,
    event?: React.BaseSyntheticEvent
  ) => unknown | Promise<unknown>;
  children: (formObj: FormObj<TFieldValues, TContext>) => React.ReactNode;
  submitButtonText?: string;
  disableSubmitButton?: boolean;
  onStateChange?: (state: FormState<TFieldValues>) => void;
  id?: string;
}

function Form<TFieldValues extends FieldValues, TContext>(
  props: FormProps<TFieldValues, TContext>
) {
  const {
    formOptions,
    onSubmit,
    children,
    submitButtonText,
    disableSubmitButton,
    onStateChange,
    id,
  } = props;
  const { handleSubmit, ...formObj } = useForm<TFieldValues, TContext>({
    mode: "onChange",
    ...formOptions,
  });
  const { formState } = formObj;
  const { isValid, isSubmitting, isDirty, dirtyFields } = formState;
  const allowSubmit = isDirty && isValid && !isSubmitting;
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  useUpdateEffect(() => {
    onStateChange?.(formState);
  }, [formState]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleFormSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    handleSubmit((data, e) => {
      const dirtyValues = R.pickBy(
        (_, key) => !!dirtyFields[key as string],
        data
      ) as Partial<typeof data>;

      return onSubmit({ values: data, modifiedValues: dirtyValues }, e);
    })().catch((error) => {
      enqueueErrorSnackbar(t("form.submit.error"), error);
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <BackdropLoading open={isSubmitting}>
      <form id={id} onSubmit={handleFormSubmit}>
        {children({ defaultValues: formOptions?.defaultValues, ...formObj })}
        {!disableSubmitButton && (
          <Button type="submit" variant="contained" disabled={!allowSubmit}>
            {submitButtonText || t("global.save")}
          </Button>
        )}
      </form>
    </BackdropLoading>
  );
}

export default Form;
