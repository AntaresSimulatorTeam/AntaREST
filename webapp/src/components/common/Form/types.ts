/* eslint-disable @typescript-eslint/no-explicit-any */
import {
  Control,
  DeepPartial,
  FieldPath,
  FieldPathValue,
  FieldValues,
  RegisterOptions,
  SetValueConfig,
  UseFormRegisterReturn,
  UseFormReturn,
} from "react-hook-form";

export interface SubmitHandlerPlus<
  // TODO Make parameter required
  TFieldValues extends FieldValues = FieldValues
> {
  values: TFieldValues;
  dirtyValues: DeepPartial<TFieldValues>;
}

export type AutoSubmitHandler<TFieldValue = any> = (
  value: TFieldValue
) => any | Promise<any>;

export type RegisterOptionsPlus<
  TFieldValues extends FieldValues = FieldValues,
  TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>
> = RegisterOptions<TFieldValues, TFieldName> & {
  onAutoSubmit?: AutoSubmitHandler<FieldPathValue<TFieldValues, TFieldName>>;
};

export type UseFormRegisterPlus<
  TFieldValues extends FieldValues = FieldValues
> = <TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>>(
  name: TFieldName,
  options?: RegisterOptionsPlus<TFieldValues, TFieldName>
) => UseFormRegisterReturn<TFieldName>;

export interface ControlPlus<
  TFieldValues extends FieldValues = FieldValues,
  TContext = any
> extends Control<TFieldValues, TContext> {
  register: UseFormRegisterPlus<TFieldValues>;
}

export type UseFormSetValues<TFieldValues extends FieldValues> = (
  values: DeepPartial<TFieldValues> | TFieldValues,
  options?: SetValueConfig
) => void;

export interface UseFormReturnPlus<
  TFieldValues extends FieldValues = FieldValues,
  TContext = any
> extends UseFormReturn<TFieldValues, TContext> {
  register: UseFormRegisterPlus<TFieldValues>;
  control: ControlPlus<TFieldValues, TContext>;
  setValues: UseFormSetValues<TFieldValues>;
  _internal: {
    initialDefaultValues: Readonly<TFieldValues> | undefined;
  };
}
