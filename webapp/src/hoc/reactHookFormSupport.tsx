/* eslint-disable @typescript-eslint/no-explicit-any */
import hoistNonReactStatics from "hoist-non-react-statics";
import React, { useMemo } from "react";
import {
  Controller,
  FieldPath,
  FieldPathValue,
  FieldValues,
  Validate,
} from "react-hook-form";
import * as R from "ramda";
import * as RA from "ramda-adjunct";
import { ControlPlus, RegisterOptionsPlus } from "../components/common/Form";
import { getComponentDisplayName } from "../utils/reactUtils";

interface ReactHookFormSupport<TValue> {
  defaultValue?: NonNullable<TValue>;
  setValueAs?: (value: any) => any;
  preValidate?: (value: any) => boolean;
}

// `...args: any` allows to be compatible with all field editors
type EventHandler = (...args: any) => void;

interface FieldEditorProps<TValue> {
  value?: TValue;
  defaultValue?: TValue;
  onChange?: EventHandler;
  onBlur?: EventHandler;
  name?: string;
}

type ReactHookFormSupportProps<
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
        | "setValueAs"
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
      const { validate } = rules;

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

      if (control && feProps.name) {
        return (
          <Controller
            control={control}
            name={feProps.name as TFieldName}
            // useForm's defaultValues take precedence
            defaultValue={(feProps.defaultValue ?? options.defaultValue) as any}
            rules={{
              ...rules,
              validate: validateWrapper,
            }}
            shouldUnregister={shouldUnregister}
            render={({
              field: { ref, onChange, onBlur, ...fieldProps },
              fieldState: { error },
            }) => (
              <FieldEditor
                {...(feProps as TProps)}
                {...fieldProps}
                onChange={(event) => {
                  // Called here instead of Controller's rules, to keep original event
                  feProps.onChange?.(event);

                  // https://github.com/react-hook-form/react-hook-form/discussions/8068#discussioncomment-2415789
                  // Data send back to hook form
                  onChange(
                    setValueAs(
                      event.target.type === "checkbox"
                        ? event.target.checked
                        : event.target.value
                    )
                  );
                }}
                onBlur={(event) => {
                  // Called here instead of Controller's rules, to keep original event
                  feProps.onBlur?.(event);

                  // Report input has been interacted (focus and blur)
                  onBlur();
                }}
                inputRef={ref}
                error={!!error}
                helperText={error?.message}
              />
            )}
          />
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
