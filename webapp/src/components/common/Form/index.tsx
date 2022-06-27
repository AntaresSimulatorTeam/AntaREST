/* eslint-disable @typescript-eslint/no-explicit-any */
import { FormEvent, useCallback, useEffect, useRef } from "react";
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
  useFormContext as useFormContextOriginal,
  UseFormProps,
  UseFormRegisterReturn,
  UseFormReturn,
  UseFormSetValue,
  UseFormUnregister,
} from "react-hook-form";
import { useTranslation } from "react-i18next";
import * as RA from "ramda-adjunct";
import { Button } from "@mui/material";
import { useUpdateEffect } from "react-use";
import * as R from "ramda";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import BackdropLoading from "../loaders/BackdropLoading";
import useDebounce from "../../../hooks/useDebounce";
import { getDirtyValues, stringToPath, toAutoSubmitConfig } from "./utils";
import useAutoUpdateRef from "../../../hooks/useAutoUpdateRef";

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
  value?: FieldPathValue<TFieldValues, TFieldName>;
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
  defaultValues?: UseFormProps<TFieldValues, TContext>["defaultValues"];
}

export type AutoSubmitConfig = { enable: boolean; wait?: number };

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

interface UseFormReturnPlus<TFieldValues extends FieldValues, TContext = any>
  extends UseFormReturn<TFieldValues, TContext> {
  register: UseFormRegisterPlus<TFieldValues>;
  defaultValues?: UseFormProps<TFieldValues, TContext>["defaultValues"];
}

export function useFormContext<
  TFieldValues extends FieldValues
>(): UseFormReturnPlus<TFieldValues> {
  return useFormContextOriginal();
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
  const { handleSubmit, formState, reset, watch } = formObj;
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
  const preventClose = useRef(false);
  const watchAllFields = watch();
  const wrapperFnsData = useAutoUpdateRef({
    fieldValues: watchAllFields,
    fieldErrors: errors,
    register: formObj.register,
    unregister: formObj.unregister,
    setValue: formObj.setValue,
    isAutoConfigEnabled: autoSubmitConfig.enable,
  });

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

  useEffect(() => {
    const listener = (event: BeforeUnloadEvent) => {
      if (preventClose.current) {
        // eslint-disable-next-line no-param-reassign
        event.returnValue = "Form not submitted yet. Sure you want to leave?"; // TODO i18n
      }
    };

    window.addEventListener("beforeunload", listener);

    return () => {
      window.removeEventListener("beforeunload", listener);
    };
  }, []);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleFormSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    handleSubmit((data, e) => {
      lastDataSubmitted.current = data;

      const dirtyValues = getDirtyValues(dirtyFields, data) as Partial<
        typeof data
      >;

      const res = [];

      if (autoSubmitConfig.enable) {
        const listeners = fieldAutoSubmitListeners.current;
        res.push(
          ...Object.keys(listeners)
            .filter((key) => R.hasPath(stringToPath(key), dirtyValues))
            .map((key) => {
              const listener = fieldAutoSubmitListeners.current[key];
              return listener?.(R.path(stringToPath(key), data));
            })
        );
      }

      if (onSubmit) {
        res.push(onSubmit({ values: data, dirtyValues }, e));
      }

      return Promise.all(res);
    })()
      .catch((error) => {
        enqueueErrorSnackbar(t("form.submit.error"), error);
      })
      .finally(() => {
        preventClose.current = false;
      });
  };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const simulateSubmitClick = useDebounce(() => {
    submitRef.current?.click();
  }, autoSubmitConfig.wait);

  const simulateSubmit = useAutoUpdateRef(() => {
    preventClose.current = true;
    simulateSubmitClick();
  });

  ////////////////////////////////////////////////////////////////
  // API
  ////////////////////////////////////////////////////////////////

  const registerWrapper = useCallback<UseFormRegisterPlus<TFieldValues>>(
    (name, options) => {
      const { register, fieldValues, fieldErrors, isAutoConfigEnabled } =
        wrapperFnsData.current;

      if (options?.onAutoSubmit) {
        fieldAutoSubmitListeners.current[name] = options.onAutoSubmit;
      }

      const newOptions = {
        ...options,
        onChange: (e: unknown) => {
          options?.onChange?.(e);
          if (isAutoConfigEnabled) {
            simulateSubmit.current();
          }
        },
      };

      const res = register(name, newOptions) as UseFormRegisterReturnPlus<
        TFieldValues,
        typeof name
      >;

      const error = fieldErrors[name];

      res.value = R.path(name.split("."), fieldValues);

      if (error) {
        res.error = true;
        if (error.message) {
          res.helperText = error.message;
        }
      }

      return res;
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const unregisterWrapper = useCallback<UseFormUnregister<TFieldValues>>(
    (name, options) => {
      const { unregister } = wrapperFnsData.current;

      if (name) {
        const names = RA.ensureArray(name) as Path<TFieldValues>[];
        names.forEach((n) => {
          delete fieldAutoSubmitListeners.current[n];
        });
      }
      return unregister(name, options);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const setValueWrapper = useCallback<UseFormSetValue<TFieldValues>>(
    (name, value, options) => {
      const { setValue, isAutoConfigEnabled } = wrapperFnsData.current;

      const newOptions: typeof options = {
        shouldDirty: isAutoConfigEnabled, // Option false by default
        ...options,
      };

      if (isAutoConfigEnabled && newOptions.shouldDirty) {
        simulateSubmit.current();
      }

      setValue(name, value, newOptions);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  const sharedProps = {
    ...formObj,
    defaultValues: config?.defaultValues,
    register: registerWrapper,
    unregister: unregisterWrapper,
    setValue: setValueWrapper,
  };

  return (
    <BackdropLoading open={isSubmitting && !autoSubmitConfig.enable}>
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
