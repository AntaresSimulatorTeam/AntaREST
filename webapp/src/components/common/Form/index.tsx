/* eslint-disable @typescript-eslint/no-explicit-any */
import { FormEvent, useCallback, useEffect, useMemo, useRef } from "react";
import {
  BatchFieldArrayUpdate,
  DeepPartial,
  FieldPath,
  FieldValues,
  FormProvider,
  FormState,
  Path,
  SubmitErrorHandler,
  useForm,
  useFormContext as useFormContextOriginal,
  UseFormProps,
  UseFormSetValue,
  UseFormUnregister,
} from "react-hook-form";
import { useTranslation } from "react-i18next";
import * as RA from "ramda-adjunct";
import {
  Box,
  Button,
  CircularProgress,
  setRef,
  SxProps,
  Theme,
} from "@mui/material";
import { useUpdateEffect } from "react-use";
import * as R from "ramda";
import clsx from "clsx";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import useDebounce from "../../../hooks/useDebounce";
import { getDirtyValues, stringToPath, toAutoSubmitConfig } from "./utils";
import useDebouncedState from "../../../hooks/useDebouncedState";
import usePrompt from "../../../hooks/usePrompt";
import { mergeSxProp } from "../../../utils/muiUtils";
import {
  SubmitHandlerPlus,
  UseFormRegisterPlus,
  UseFormReturnPlus,
} from "./types";
import useAutoUpdateRef from "../../../hooks/useAutoUpdateRef";
import FormContext from "./FormContext";

export type AutoSubmitConfig = { enable: boolean; wait?: number };

export interface FormProps<
  TFieldValues extends FieldValues = FieldValues,
  TContext = any
> extends Omit<React.HTMLAttributes<HTMLFormElement>, "onSubmit" | "children"> {
  config?: UseFormProps<TFieldValues, TContext>;
  onSubmit?: (
    data: SubmitHandlerPlus<TFieldValues>,
    event?: React.BaseSyntheticEvent
  ) => void | Promise<any>;
  onSubmitError?: SubmitErrorHandler<TFieldValues>;
  children:
    | ((formApi: UseFormReturnPlus<TFieldValues, TContext>) => React.ReactNode)
    | React.ReactNode;
  submitButtonText?: string;
  hideSubmitButton?: boolean;
  onStateChange?: (state: FormState<TFieldValues>) => void;
  autoSubmit?: boolean | AutoSubmitConfig;
  disableLoader?: boolean;
  sx?: SxProps<Theme>;
  apiRef?: React.Ref<UseFormReturnPlus<TFieldValues, TContext> | undefined>;
}

export function useFormContextPlus<TFieldValues extends FieldValues>() {
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
    disableLoader,
    className,
    sx,
    apiRef,
    ...formProps
  } = props;

  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();
  const submitRef = useRef<HTMLButtonElement>(null);
  const autoSubmitConfig = toAutoSubmitConfig(autoSubmit);
  const fieldAutoSubmitListeners = useRef<
    Record<string, ((v: any) => any | Promise<any>) | undefined>
  >({});
  const [showLoader, setShowLoader] = useDebouncedState(false, 750);
  const lastSubmittedData = useRef<TFieldValues>();
  const preventClose = useRef(false);
  const fieldsChangeDuringAutoSubmitting = useRef<FieldPath<TFieldValues>[]>(
    []
  );
  const contextValue = useMemo(
    () => ({ isAutoSubmitEnabled: autoSubmitConfig.enable }),
    [autoSubmitConfig.enable]
  );

  const formApiOriginal = useForm<TFieldValues, TContext>({
    mode: "onChange",
    delayError: 750,
    ...config,
    defaultValues: RA.isFunction(config?.defaultValues)
      ? () => {
          const fn = config?.defaultValues as () => Promise<TFieldValues>;
          return fn().catch((err) => {
            enqueueErrorSnackbar(t("form.asyncDefaultValues.error"), err);
            throw err;
          });
        }
      : config?.defaultValues,
  });

  const {
    register,
    unregister,
    getValues,
    setValue,
    control,
    handleSubmit,
    formState,
    reset,
  } = formApiOriginal;

  // * /!\ `formState` is a proxy
  const { isSubmitting, isDirty, dirtyFields } = formState;
  // Don't add `isValid` because we need to trigger fields validation.
  // In case we have invalid default value for example.
  const isSubmitAllowed = isDirty && !isSubmitting;
  // To use it in form API wrapper functions without need to add the value in `useMemo`'s deps
  const isSubmittingRef = useAutoUpdateRef(isSubmitting);
  const isAutoSubmitEnabledRef = useAutoUpdateRef(autoSubmitConfig.enable);

  useUpdateEffect(() => {
    setShowLoader(isSubmitting);
    if (isSubmitting) {
      setShowLoader.flush();
    }
  }, [isSubmitting]);

  useUpdateEffect(
    () => {
      onStateChange?.(formState);

      // It's recommended to reset inside useEffect after submission: https://react-hook-form.com/api/useform/reset
      if (formState.isSubmitSuccessful) {
        const valuesToSetAfterReset = getValues(
          fieldsChangeDuringAutoSubmitting.current
        );

        // Reset only dirty values make issue with `getValues` and `watch` which only return reset values
        reset(lastSubmittedData.current);

        fieldsChangeDuringAutoSubmitting.current.forEach((fieldName, index) => {
          setValue(fieldName, valuesToSetAfterReset[index], {
            shouldDirty: true,
          });
        });

        fieldsChangeDuringAutoSubmitting.current = [];
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
        event.returnValue = t("form.submit.inProgress");
      }
    };

    window.addEventListener("beforeunload", listener);

    return () => {
      window.removeEventListener("beforeunload", listener);
    };
  }, [t]);

  usePrompt(t("form.submit.inProgress"), preventClose.current);

  ////////////////////////////////////////////////////////////////
  // Submit
  ////////////////////////////////////////////////////////////////

  const submit = () => {
    const callback = handleSubmit(function onValid(data, event) {
      lastSubmittedData.current = data;

      const dirtyValues = getDirtyValues(dirtyFields, data) as DeepPartial<
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
        res.push(onSubmit({ values: data, dirtyValues }, event));
      }

      return Promise.all(res)
        .catch((error) => {
          enqueueErrorSnackbar(t("form.submit.error"), error);
        })
        .finally(() => {
          preventClose.current = false;
        });
    }, onSubmitError);

    return callback();
  };

  const submitDebounced = useDebounce(submit, autoSubmitConfig.wait);

  const requestSubmit = useCallback(() => {
    preventClose.current = true;
    submitDebounced();
  }, [submitDebounced]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleFormSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    submit();
  };

  ////////////////////////////////////////////////////////////////
  // API
  ////////////////////////////////////////////////////////////////

  const formApiShared = useMemo(
    () => {
      if (!isAutoSubmitEnabledRef.current) {
        return formApiOriginal;
      }

      const registerWrapper: UseFormRegisterPlus<TFieldValues> = (
        name,
        options
      ) => {
        if (options?.onAutoSubmit) {
          fieldAutoSubmitListeners.current[name] = options.onAutoSubmit;
        }

        const newOptions: typeof options = {
          ...options,
          onChange: (event: unknown) => {
            options?.onChange?.(event);
            if (isAutoSubmitEnabledRef.current) {
              if (
                isSubmittingRef.current &&
                !fieldsChangeDuringAutoSubmitting.current.includes(name)
              ) {
                fieldsChangeDuringAutoSubmitting.current.push(name);
              }

              requestSubmit();
            }
          },
        };

        return register(name, newOptions);
      };

      const unregisterWrapper: UseFormUnregister<TFieldValues> = (
        name,
        options
      ) => {
        if (name) {
          const names = RA.ensureArray(name) as Path<TFieldValues>[];
          names.forEach((n) => {
            delete fieldAutoSubmitListeners.current[n];
          });
        }
        return unregister(name, options);
      };

      const setValueWrapper: UseFormSetValue<TFieldValues> = (
        name,
        value,
        options
      ) => {
        const newOptions: typeof options = {
          shouldDirty: isAutoSubmitEnabledRef.current, // Option false by default
          ...options,
        };

        if (isAutoSubmitEnabledRef.current && newOptions.shouldDirty) {
          if (isSubmittingRef.current) {
            fieldsChangeDuringAutoSubmitting.current.push(name);
          }
          // If it's a new value
          if (value !== getValues(name)) {
            requestSubmit();
          }
        }

        setValue(name, value, newOptions);
      };

      // Mutate the `control` object.
      // Spreading cannot be used because getters and setters would be removed.
      (() => {
        control.register = registerWrapper;
        control.unregister = unregisterWrapper;

        const updateFieldArrayOriginal =
          control._updateFieldArray.bind(control);
        const updateFieldArrayWrapper: BatchFieldArrayUpdate = (...args) => {
          updateFieldArrayOriginal(...args);
          if (isAutoSubmitEnabledRef.current) {
            requestSubmit();
          }
        };
        // Used by `useFieldArray` hook's methods (`append`, `remove`...)
        control._updateFieldArray = updateFieldArrayWrapper;
      })();

      return {
        ...formApiOriginal,
        register: registerWrapper,
        unregister: unregisterWrapper,
        setValue: setValueWrapper,
      };
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [formApiOriginal, requestSubmit]
  );

  useEffect(() => setRef(apiRef, formApiShared));

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      {...formProps}
      sx={mergeSxProp({ pt: 1 }, sx)}
      component="form"
      onSubmit={handleFormSubmit}
      className={clsx("Form", className)}
    >
      {showLoader && !disableLoader && (
        <Box
          sx={{
            position: "sticky",
            top: 0,
            right: 0,
            height: 0,
            textAlign: "right",
          }}
          className="Form__Loader"
        >
          <CircularProgress color="secondary" size={20} sx={{ mr: 1 }} />
        </Box>
      )}
      <FormContext.Provider value={contextValue}>
        {RA.isFunction(children) ? (
          children(formApiShared)
        ) : (
          <FormProvider {...formApiShared}>{children}</FormProvider>
        )}
      </FormContext.Provider>
      {!hideSubmitButton && !autoSubmitConfig.enable && (
        <Button
          type="submit"
          variant="contained"
          disabled={!isSubmitAllowed}
          ref={submitRef}
        >
          {submitButtonText || t("global.save")}
        </Button>
      )}
    </Box>
  );
}

export default Form;
