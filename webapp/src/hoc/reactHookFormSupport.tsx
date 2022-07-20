/* eslint-disable @typescript-eslint/no-explicit-any */
import hoistNonReactStatics from "hoist-non-react-statics";
import React from "react";
import { Controller, FieldPath, FieldValues } from "react-hook-form";
import * as R from "ramda";
import { ControlPlus, RegisterOptionsPlus } from "../components/common/Form";
import { getComponentDisplayName } from "../utils/reactUtils";

interface ReactHookFormSupport<TValue> {
  defaultValue?: NonNullable<TValue>;
  setValueAs?: (value: any) => any;
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
        "valueAsNumber" | "valueAsDate" | "setValueAs" | "disabled"
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
  const { defaultValue, setValueAs = R.identity } = options;

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
      const { control, rules, shouldUnregister, ...fieldEditorProps } = props;
      const { name, onChange, onBlur } = fieldEditorProps;

      if (control && name) {
        return (
          <Controller
            control={control}
            name={name as TFieldName}
            defaultValue={defaultValue as any} // useForm's defaultValues take precedence
            rules={{
              ...rules,
              onChange: (event) => {
                onChange?.(event);
                rules?.onChange?.(event);
              },
              onBlur: (event) => {
                onBlur?.(event);
                rules?.onBlur?.(event);
              },
            }}
            shouldUnregister={shouldUnregister}
            render={({
              field: { ref, onChange, ...fieldProps },
              fieldState: { error },
            }) => (
              <FieldEditor
                {...(fieldEditorProps as TProps)}
                {...fieldProps}
                onChange={(event) => {
                  onChange(
                    setValueAs(
                      event.target.type === "checkbox"
                        ? event.target.checked
                        : event.target.value
                    )
                  );
                }}
                inputRef={ref}
                error={!!error}
                helperText={error?.message}
              />
            )}
          />
        );
      }

      return <FieldEditor {...(fieldEditorProps as TProps)} />;
    }

    ReactHookFormSupport.displayName = `ReactHookFormSupport(${getComponentDisplayName(
      FieldEditor
    )})`;

    return hoistNonReactStatics(ReactHookFormSupport, FieldEditor);
  }

  return wrapWithReactHookFormSupport;
}

export default reactHookFormSupport;
