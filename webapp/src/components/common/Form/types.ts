/* eslint-disable @typescript-eslint/no-explicit-any */
import {
  Control,
  DeepPartial,
  DefaultValues,
  FieldPath,
  FieldPathValue,
  FieldValues,
  RegisterOptions,
  UseFormProps,
  UseFormRegisterReturn,
  UseFormReturn,
} from "react-hook-form";

export interface SubmitHandlerPlus<
  TFieldValues extends FieldValues = FieldValues
> {
  values: TFieldValues;
  dirtyValues: DeepPartial<TFieldValues>;
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

export interface UseFormPropsPlus<
  TFieldValues extends FieldValues = FieldValues,
  TContext = any
> extends UseFormProps<TFieldValues, TContext> {
  asyncDefaultValues?: () => Promise<DefaultValues<TFieldValues>>;
}

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
  _showSkeleton: boolean;
}

export interface UseFormReturnPlus<
  TFieldValues extends FieldValues = FieldValues,
  TContext = any
> extends UseFormReturn<TFieldValues, TContext> {
  register: UseFormRegisterPlus<TFieldValues>;
  control: ControlPlus<TFieldValues, TContext>;
  /**
   * @deprecated
   */
  defaultValues?: UseFormProps<TFieldValues, TContext>["defaultValues"];
}
