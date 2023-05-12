/* eslint-disable @typescript-eslint/no-explicit-any */
import {
  Control,
  DeepPartial,
  FieldPath,
  FieldPathValue,
  FieldValues,
  RegisterOptions,
  UseFormRegisterReturn,
  UseFormReturn,
} from "react-hook-form";
import { O } from "ts-toolbelt";

export interface SubmitHandlerPlus<
  // TODO Make parameter required
  TFieldValues extends FieldValues = FieldValues
> {
  values: TFieldValues;
  dirtyValues: DeepPartial<TFieldValues>;
}

export type AutoSubmitHandler<
  TFieldValues extends FieldValues = FieldValues,
  TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>
> = (value: FieldPathValue<TFieldValues, TFieldName>) => any | Promise<any>;

export type RegisterOptionsPlus<
  TFieldValues extends FieldValues = FieldValues,
  TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>
> = RegisterOptions<TFieldValues, TFieldName> & {
  onAutoSubmit?: AutoSubmitHandler<TFieldValues, TFieldName>;
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

export interface UseFormReturnPlus<
  TFieldValues extends FieldValues = FieldValues,
  TContext = any
> extends UseFormReturn<TFieldValues, TContext> {
  register: UseFormRegisterPlus<TFieldValues>;
  control: ControlPlus<TFieldValues, TContext>;
}

export type DefaultValuesFix<TFieldValues extends FieldValues> = O.Partial<
  TFieldValues,
  "deep"
>;
