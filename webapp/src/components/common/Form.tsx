/* eslint-disable @typescript-eslint/no-explicit-any */
import { FormEvent, useCallback, useRef } from "react";
import {
  FieldPath,
  FieldPathValue,
  FieldValues,
  FormProvider,
  FormState,
  Path,
  RegisterOptions,
  UnpackNestedValue,
  useForm,
  UseFormProps,
  UseFormRegisterReturn,
  UseFormReturn,
  UseFormUnregister,
} from "react-hook-form";
import { useTranslation } from "react-i18next";
import * as R from "ramda";
import * as RA from "ramda-adjunct";
import { Button } from "@mui/material";
import { useUpdateEffect } from "react-use";
import useEnqueueErrorSnackbar from "../../hooks/useEnqueueErrorSnackbar";
import BackdropLoading from "./loaders/BackdropLoading";
import useDebounce from "../../hooks/useDebounce";

export interface SubmitHandlerData<
  TFieldValues extends FieldValues = FieldValues
> {
  values: UnpackNestedValue<TFieldValues>;
  dirtyValues: Partial<UnpackNestedValue<TFieldValues>>;
}

export type AutoSubmitHandler<
  TFieldValues extends FieldValues = FieldValues,
  TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>
> = (value: FieldPathValue<TFieldValues, TFieldName>) => any | Promise<any>;

export interface UseFormRegisterReturnPlus<
  TFieldValues extends FieldValues = FieldValues,
  TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>
> extends UseFormRegisterReturn {
  defaultValue?: FieldPathValue<TFieldValues, TFieldName>;
  error?: boolean;
  helperText?: string;
}

export type UseFormRegisterPlus<
  TFieldValues extends FieldValues = FieldValues
> = <TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>>(
  name: TFieldName,
  options?: RegisterOptions<TFieldValues, TFieldName> & {
    onAutoSubmit?: AutoSubmitHandler<TFieldValues, TFieldName>;
  }
) => UseFormRegisterReturnPlus;

export interface FormObj<
  TFieldValues extends FieldValues = FieldValues,
  TContext = any
> extends UseFormReturn<TFieldValues, TContext> {
  register: UseFormRegisterPlus<TFieldValues>;
  defaultValues: UseFormProps<TFieldValues, TContext>["defaultValues"];
}

type AutoSubmitConfig = { enable: boolean; wait?: number };

export interface FormProps<
  TFieldValues extends FieldValues = FieldValues,
  TContext = any
> {
  config?: UseFormProps<TFieldValues, TContext>;
  onSubmit?: (
    data: SubmitHandlerData<TFieldValues>,
    event?: React.BaseSyntheticEvent
  ) => any | Promise<any>;
  children:
    | ((formObj: FormObj<TFieldValues, TContext>) => React.ReactNode)
    | React.ReactNode;
  submitButtonText?: string;
  hideSubmitButton?: boolean;
  onStateChange?: (state: FormState<TFieldValues>) => void;
  autoSubmit?: boolean | AutoSubmitConfig;
  id?: string;
}

function toAutoSubmitConfig(
  value: FormProps["autoSubmit"]
): Required<AutoSubmitConfig> {
  return {
    wait: 1000,
    ...(RA.isPlainObj(value) ? value : { enable: !!value }),
  };
}

function Form<TFieldValues extends FieldValues, TContext>(
  props: FormProps<TFieldValues, TContext>
) {
  const {
    config,
    onSubmit,
    children,
    submitButtonText,
    hideSubmitButton,
    onStateChange,
    autoSubmit,
    id,
  } = props;
  const formObj = useForm<TFieldValues, TContext>({
    mode: "onChange",
    ...config,
  });
  const { handleSubmit, formState, register, unregister, reset } = formObj;
  const { isValid, isSubmitting, isDirty, dirtyFields, errors } = formState;
  const allowSubmit = isDirty && isValid && !isSubmitting;
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();
  const submitRef = useRef<HTMLButtonElement>(null);
  const autoSubmitConfig = toAutoSubmitConfig(autoSubmit);
  const fieldAutoSubmitListeners = useRef<
    Record<string, ((v: any) => any | Promise<any>) | undefined>
  >({});
  const lastDataSubmitted = useRef<UnpackNestedValue<TFieldValues>>();

  useUpdateEffect(
    () => {
      onStateChange?.(formState);

      // It's recommended to reset inside useEffect after submission: https://react-hook-form.com/api/useform/reset
      if (formState.isSubmitSuccessful) {
        reset(lastDataSubmitted.current);
      }
    },
    // Entire `formState` must be put in the deps: https://react-hook-form.com/api/useform/formstate
    [formState]
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleFormSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    handleSubmit((data, e) => {
      lastDataSubmitted.current = data;

      const dirtyValues = R.pickBy(
        (_, key) => !!dirtyFields[key as string],
        data
      ) as Partial<typeof data>;

      const res = [];

      if (autoSubmitConfig.enable) {
        res.push(
          ...Object.keys(dirtyValues).map((fieldName) => {
            const listener = fieldAutoSubmitListeners.current[fieldName];
            return listener?.(data[fieldName]);
          })
        );
      }

      if (onSubmit) {
        res.push(onSubmit({ values: data, dirtyValues }, e));
      }

      return Promise.all(res);
    })().catch((error) => {
      enqueueErrorSnackbar(t("form.submit.error"), error);
    });
  };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const simulateSubmit = useDebounce(() => {
    submitRef.current?.click();
  }, autoSubmitConfig.wait);

  const registerWrapper = useCallback<UseFormRegisterPlus<TFieldValues>>(
    (name, options) => {
      if (options?.onAutoSubmit) {
        fieldAutoSubmitListeners.current[name] = options.onAutoSubmit;
      }

      const newOptions = {
        ...options,
        onChange: (e: unknown) => {
          options?.onChange?.(e);
          if (autoSubmitConfig.enable) {
            simulateSubmit();
          }
        },
      };

      const res = register(name, newOptions) as UseFormRegisterReturnPlus<
        TFieldValues,
        typeof name
      >;

      const error = errors[name];

      if (RA.isNotNil(config?.defaultValues?.[name])) {
        res.defaultValue = config?.defaultValues?.[name];
      }

      if (error) {
        res.error = true;
        if (error.message) {
          res.helperText = error.message;
        }
      }

      return res;
    },
    [
      autoSubmitConfig.enable,
      config?.defaultValues,
      errors,
      register,
      simulateSubmit,
    ]
  );

  const unregisterWrapper = useCallback<UseFormUnregister<TFieldValues>>(
    (name, options) => {
      if (name) {
        const names = RA.ensureArray(name) as Path<TFieldValues>[];
        names.forEach((n) => {
          delete fieldAutoSubmitListeners.current[n];
        });
      }
      return unregister(name, options);
    },
    [unregister]
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  const sharedProps = {
    ...formObj,
    defaultValues: config?.defaultValues,
    register: registerWrapper,
    unregister: unregisterWrapper,
  };

  return (
    <BackdropLoading open={isSubmitting || !autoSubmitConfig.enable}>
      <form id={id} onSubmit={handleFormSubmit}>
        {RA.isFunction(children) ? (
          children(sharedProps)
        ) : (
          <FormProvider {...sharedProps}>{children}</FormProvider>
        )}
        <Button
          sx={[
            (hideSubmitButton || autoSubmitConfig.enable) && {
              display: "none",
            },
          ]}
          type="submit"
          variant="contained"
          disabled={!allowSubmit}
          ref={submitRef}
        >
          {submitButtonText || t("global.save")}
        </Button>
      </form>
    </BackdropLoading>
  );
}

export default Form;
