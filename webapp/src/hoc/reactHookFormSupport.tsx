/* eslint-disable @typescript-eslint/no-explicit-any */
import hoistNonReactStatics from "hoist-non-react-statics";
import React, { useMemo } from "react";
import {
  Controller,
  ControllerRenderProps,
  FieldPath,
  FieldPathValue,
  FieldValues,
  Validate,
} from "react-hook-form";
import * as R from "ramda";
import * as RA from "ramda-adjunct";
import { Skeleton } from "@mui/material";
import { getComponentDisplayName } from "../utils/reactUtils";
import { FakeBlurEventHandler, FakeChangeEventHandler } from "../utils/feUtils";
import {
  ControlPlus,
  RegisterOptionsPlus,
} from "../components/common/Form/types";

interface ReactHookFormSupport<TValue> {
  defaultValue?: NonNullable<TValue> | ((props: any) => NonNullable<TValue>);
  setValueAs?: (value: any) => any;
  preValidate?: (value: any) => boolean;
}

// `...args: any` allows to be compatible with all field editors
type EventHandler = (...args: any[]) => void;

interface FieldEditorProps<TValue> {
  value?: TValue;
  defaultValue?: TValue;
  onChange?: EventHandler;
  onBlur?: EventHandler;
  name?: string;
  disabled?: boolean;
  // inputRef?: any;
  // error?: boolean;
  // helperText?: string;
}

export type ReactHookFormSupportProps<
  TFieldValues extends FieldValues = FieldValues,
  TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
  TContext = any
> =
  | {
      control: ControlPlus<TFieldValues, TContext>;
      rules?: Omit<
        RegisterOptionsPlus<TFieldValues, TFieldName>,
        // cf. UseControllerProps#rules
        | "valueAsNumber"
        | "valueAsDate"
        | "disabled"
        // Not necessary
        | "onChange"
        | "onBlur"
      >;
      shouldUnregister?: boolean;
      name: TFieldName;
    }
  | {
      control?: undefined;
      rules?: never;
      shouldUnregister?: never;
    };

function reactHookFormSupport<TValue>(
  options: ReactHookFormSupport<TValue> = {}
) {
  const { preValidate, setValueAs = R.identity } = options;

  function wrapWithReactHookFormSupport<
    TProps extends FieldEditorProps<TValue>
  >(FieldEditor: React.ComponentType<TProps>) {
    function ReactHookFormSupport<
      TFieldValues extends FieldValues = FieldValues,
      TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
      TContext = any
    >(
      props: ReactHookFormSupportProps<TFieldValues, TFieldName, TContext> &
        TProps
    ) {
      const { control, rules = {}, shouldUnregister, ...feProps } = props;

      const {
        validate,
        setValueAs: setValueAsFromRules = R.identity,
        ...restRules
      } = rules;

      ////////////////////////////////////////////////////////////////
      // Event Handlers
      ////////////////////////////////////////////////////////////////

      const handleChange =
        (internalOnChange: ControllerRenderProps["onChange"]) =>
        (event: FakeChangeEventHandler) => {
          if (feProps.disabled) {
            return;
          }

          // Called here instead of Controller's rules, to keep original event
          feProps.onChange?.(event);

          // https://github.com/react-hook-form/react-hook-form/discussions/8068#discussioncomment-2415789
          // Data send back to hook form
          internalOnChange(
            setValueAsFromRules(
              setValueAs(
                event.target.type === "checkbox"
                  ? event.target.checked
                  : event.target.value
              )
            )
          );
        };

      const handleBlur =
        (internalOnBlur: ControllerRenderProps["onBlur"]) =>
        (event: FakeBlurEventHandler) => {
          if (feProps.disabled) {
            return;
          }

          // Called here instead of Controller's rules, to keep original event
          feProps.onBlur?.(event);

          // Report input has been interacted (focus and blur)
          internalOnBlur();
        };

      ////////////////////////////////////////////////////////////////
      // Utils
      ////////////////////////////////////////////////////////////////

      const validateWrapper = useMemo<
        RegisterOptionsPlus<TFieldValues, TFieldName>["validate"]
      >(() => {
        if (preValidate) {
          if (RA.isFunction(validate)) {
            return (v) => preValidate?.(v) && validate(v);
          }

          if (RA.isPlainObj(validate)) {
            return Object.keys(validate).reduce((acc, key) => {
              acc[key] = (v) => preValidate?.(v) && validate[key](v);
              return acc;
            }, {} as Record<string, Validate<FieldPathValue<TFieldValues, TFieldName>>>);
          }

          return preValidate;
        }
        return validate;
      }, [validate]);

      const getDefaultValuesFromOptions = () => {
        const { defaultValue } = options;
        return RA.isFunction(defaultValue)
          ? defaultValue(feProps)
          : defaultValue;
      };

      ////////////////////////////////////////////////////////////////
      // JSX
      ////////////////////////////////////////////////////////////////

      if (control && feProps.name) {
        const field = (
          <Controller
            control={control}
            name={feProps.name as TFieldName}
            // useForm's defaultValues take precedence
            defaultValue={
              (feProps.defaultValue ?? getDefaultValuesFromOptions()) as any
            }
            rules={{ ...restRules, validate: validateWrapper }}
            shouldUnregister={shouldUnregister}
            render={({
              field: { ref, onChange, onBlur, ...fieldProps },
              fieldState: { error },
            }) => (
              <FieldEditor
                {...(feProps as TProps)}
                {...fieldProps}
                onChange={handleChange(onChange)}
                onBlur={handleBlur(onBlur)}
                inputRef={ref}
                error={!!error}
                helperText={error?.message}
              />
            )}
          />
        );

        return control._showSkeleton ? (
          <Skeleton variant="rectangular" sx={{ borderRadius: "5px" }}>
            {field}
          </Skeleton>
        ) : (
          field
        );
      }

      return <FieldEditor {...(feProps as TProps)} />;
    }

    ReactHookFormSupport.displayName = `ReactHookFormSupport(${getComponentDisplayName(
      FieldEditor
    )})`;

    return hoistNonReactStatics(ReactHookFormSupport, FieldEditor);
  }

  return wrapWithReactHookFormSupport;
}

export default reactHookFormSupport;
