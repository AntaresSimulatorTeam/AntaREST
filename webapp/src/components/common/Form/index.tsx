/* eslint-disable @typescript-eslint/no-explicit-any */
import { FormEvent, useCallback, useEffect, useMemo, useRef } from "react";
import {
  Control,
  FieldPath,
  FieldPathValue,
  FieldValues,
  FormProvider,
  FormState,
  Path,
  RegisterOptions,
  SubmitErrorHandler,
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
import { Box, Button, CircularProgress } from "@mui/material";
import { useUpdateEffect } from "react-use";
import * as R from "ramda";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import useDebounce from "../../../hooks/useDebounce";
import { getDirtyValues, stringToPath, toAutoSubmitConfig } from "./utils";
import useDebouncedState from "../../../hooks/useDebouncedState";

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

export interface RegisterOptionsPlus<
  TFieldValues extends FieldValues = FieldValues,
  TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>
> extends RegisterOptions<TFieldValues, TFieldName> {
  onAutoSubmit?: AutoSubmitHandler<TFieldValues, TFieldName>;
}

export type UseFormRegisterPlus<
  TFieldValues extends FieldValues = FieldValues
> = <TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>>(
  name: TFieldName,
  options?: RegisterOptionsPlus<TFieldValues, TFieldName>
) => UseFormRegisterReturn;

export interface ControlPlus<
  TFieldValues extends FieldValues = FieldValues,
  TContext = any
> extends Control<TFieldValues, TContext> {
  register: UseFormRegisterPlus<TFieldValues>;
}

export interface UseFormReturnPlus<
  TFieldValues extends FieldValues = FieldValues,
  TContext = any
> extends UseFormReturn<TFieldValues, TContext> {
  register: UseFormRegisterPlus<TFieldValues>;
  control: ControlPlus<TFieldValues, TContext>;
  defaultValues?: UseFormProps<TFieldValues, TContext>["defaultValues"];
}

export type AutoSubmitConfig = { enable: boolean; wait?: number };

export interface FormProps<
  TFieldValues extends FieldValues = FieldValues,
  TContext = any
> extends Omit<React.HTMLAttributes<HTMLFormElement>, "onSubmit"> {
  config?: UseFormProps<TFieldValues, TContext>;
  onSubmit?: (
    data: SubmitHandlerData<TFieldValues>,
    event?: React.BaseSyntheticEvent
  ) => any | Promise<any>;
  onSubmitError?: SubmitErrorHandler<TFieldValues>;
  children:
    | ((formObj: UseFormReturnPlus<TFieldValues, TContext>) => React.ReactNode)
    | React.ReactNode;
  submitButtonText?: string;
  hideSubmitButton?: boolean;
  onStateChange?: (state: FormState<TFieldValues>) => void;
  autoSubmit?: boolean | AutoSubmitConfig;
}

export function useFormContext<TFieldValues extends FieldValues>() {
  return useFormContextOriginal() as UseFormReturnPlus<TFieldValues>;
}

function Form<TFieldValues extends FieldValues, TContext>(
  props: FormProps<TFieldValues, TContext>
) {
  const {
    config,
    onSubmit,
    onSubmitError,
    children,
    submitButtonText,
    hideSubmitButton,
    onStateChange,
    autoSubmit,
    ...formProps
  } = props;

  const formObj = useForm<TFieldValues, TContext>({
    mode: "onChange",
    delayError: 750,
    ...config,
  });

  const {
    getValues,
    register,
    unregister,
    setValue,
    control,
    handleSubmit,
    formState,
    reset,
  } = formObj;
  // * /!\ `formState` is a proxy
  const { isSubmitting, isDirty, dirtyFields } = formState;
  // Don't add `isValid` because we need to trigger fields validation.
  // In case we have invalid default value for example.
  const isSubmitAllowed = isDirty && !isSubmitting;
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();
  const submitRef = useRef<HTMLButtonElement>(null);
  const autoSubmitConfig = toAutoSubmitConfig(autoSubmit);
  const fieldAutoSubmitListeners = useRef<
    Record<string, ((v: any) => any | Promise<any>) | undefined>
  >({});
  const preventClose = useRef(false);
  const [showLoader, setLoader] = useDebouncedState(false, 750);

  useUpdateEffect(() => {
    setLoader(isSubmitting);
    if (isSubmitting) {
      setLoader.flush();
    }
  }, [isSubmitting]);

  useUpdateEffect(
    () => {
      onStateChange?.(formState);

      // It's recommended to reset inside useEffect after submission: https://react-hook-form.com/api/useform/reset
      if (formState.isSubmitSuccessful) {
        reset(getValues());
      }
    },
    // Entire `formState` must be put in the deps: https://react-hook-form.com/api/useform/formstate
    [formState]
  );

  // Prevent browser close if a submit is pending (auto submit enabled)
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

    handleSubmit(function onValid(data, e) {
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
    }, onSubmitError)()
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

  const simulateSubmit = useCallback(() => {
    preventClose.current = true;
    simulateSubmitClick();
  }, [simulateSubmitClick]);

  ////////////////////////////////////////////////////////////////
  // API
  ////////////////////////////////////////////////////////////////

  const registerWrapper = useCallback<UseFormRegisterPlus<TFieldValues>>(
    (name, options) => {
      if (options?.onAutoSubmit) {
        fieldAutoSubmitListeners.current[name] = options.onAutoSubmit;
      }

      const newOptions: typeof options = {
        ...options,
        onChange: (event: any) => {
          options?.onChange?.(event);
          if (autoSubmitConfig.enable) {
            simulateSubmit();
          }
        },
      };

      return register(name, newOptions);
    },
    [autoSubmitConfig.enable, register, simulateSubmit]
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

  const setValueWrapper = useCallback<UseFormSetValue<TFieldValues>>(
    (name, value, options) => {
      const newOptions: typeof options = {
        shouldDirty: autoSubmitConfig.enable, // Option false by default
        ...options,
      };

      if (autoSubmitConfig.enable && newOptions.shouldDirty) {
        simulateSubmit();
      }

      setValue(name, value, newOptions);
    },
    [autoSubmitConfig.enable, setValue, simulateSubmit]
  );

  const controlWrapper = useMemo<ControlPlus<TFieldValues, TContext>>(() => {
    // Don't use spread to keep getters and setters
    control.register = registerWrapper;
    control.unregister = unregisterWrapper;
    return control;
  }, [control, registerWrapper, unregisterWrapper]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  const sharedProps = {
    ...formObj,
    formState,
    defaultValues: config?.defaultValues,
    register: registerWrapper,
    unregister: unregisterWrapper,
    setValue: setValueWrapper,
    control: controlWrapper,
  };

  return (
    <form {...formProps} onSubmit={handleFormSubmit}>
      {showLoader && (
        <Box
          sx={{
            position: "sticky",
            top: 0,
            right: 0,
            height: 0,
            textAlign: "right",
          }}
        >
          <CircularProgress color="secondary" size={20} sx={{ mr: 1 }} />
        </Box>
      )}
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
        disabled={!isSubmitAllowed}
        ref={submitRef}
      >
        {submitButtonText || t("global.save")}
      </Button>
    </form>
  );
}

export default Form;
