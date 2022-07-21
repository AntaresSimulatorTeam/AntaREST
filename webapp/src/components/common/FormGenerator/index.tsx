import * as R from "ramda";
import { v4 as uuidv4 } from "uuid";
import {
  DeepPartial,
  FieldValues,
  Path,
  UnpackNestedValue,
} from "react-hook-form";
import { useTranslation } from "react-i18next";
import { SxProps, Theme } from "@mui/material";
import { useMemo } from "react";
import SelectFE, { SelectFEProps } from "../fieldEditors/SelectFE";
import StringFE from "../fieldEditors/StringFE";
import Fieldset from "../Fieldset";
import { RegisterOptionsPlus, useFormContext } from "../Form";
import NumberFE from "../fieldEditors/NumberFE";
import SwitchFE from "../fieldEditors/SwitchFE";
import BooleanFE, { BooleanFEProps } from "../fieldEditors/BooleanFE";

export type GeneratorFieldType =
  | "text"
  | "number"
  | "select"
  | "switch"
  | "boolean";

export interface IGeneratorField<T> {
  type: GeneratorFieldType;
  name: Path<T> & (string | undefined);
  label: string;
  sx?: SxProps<Theme> | undefined;
  noDataValue?: any;
  rules?: (
    defaultValues?: UnpackNestedValue<DeepPartial<T>> | undefined,
    noDataValue?: any
  ) =>
    | Omit<
        RegisterOptionsPlus<T, Path<T> & (string | undefined)>,
        "disabled" | "valueAsNumber" | "valueAsDate" | "setValueAs"
      >
    | undefined;
}

export interface SelectField<T> extends IGeneratorField<T> {
  options: SelectFEProps["options"];
}

export interface BooleanField<T> extends IGeneratorField<T> {
  falseText: BooleanFEProps["falseText"];
  trueText: BooleanFEProps["trueText"];
}

export type IGeneratorFieldType<T> =
  | IGeneratorField<T>
  | SelectField<T>
  | BooleanField<T>;

export interface IFieldsetType<T> {
  translationId: string;
  fields: Array<IGeneratorFieldType<T>>;
}

export type IFormGenerator<T> = Array<IFieldsetType<T>>;

export interface FormGeneratorProps<T> {
  jsonTemplate: IFormGenerator<T>;
}

function formateFieldset<T>(fieldset: IFieldsetType<T>) {
  const { fields, ...otherProps } = fieldset;
  const formatedFields = fields.map((field) => ({ ...field, id: uuidv4() }));
  return { ...otherProps, fields: formatedFields, id: uuidv4() };
}

export default function FormGenerator<T extends FieldValues>(
  props: FormGeneratorProps<T>
) {
  const { jsonTemplate } = props;
  const formatedTemplate = useMemo(
    () => jsonTemplate.map(formateFieldset),
    [jsonTemplate]
  );
  const [t] = useTranslation();
  const { control, defaultValues } = useFormContext<T>();

  return (
    <>
      {formatedTemplate.map((fieldset) => (
        <Fieldset key={fieldset.id} legend={t(fieldset.translationId)}>
          {fieldset.fields.map((field) => {
            const { id, rules, type, noDataValue, ...otherProps } = field;
            const vRules = rules
              ? rules(defaultValues, noDataValue)
              : undefined;
            return (
              <>
                {R.cond([
                  [
                    R.equals("text"),
                    () => (
                      <StringFE
                        key={id}
                        {...otherProps}
                        variant="filled"
                        control={control}
                        rules={vRules}
                      />
                    ),
                  ],
                  [
                    R.equals("number"),
                    () => (
                      <NumberFE
                        key={id}
                        {...otherProps}
                        variant="filled"
                        control={control}
                        rules={vRules}
                      />
                    ),
                  ],
                  [
                    R.equals("switch"),
                    () => (
                      <SwitchFE
                        key={id}
                        {...otherProps}
                        control={control}
                        rules={vRules}
                      />
                    ),
                  ],
                  [
                    R.equals("boolean"),
                    () => (
                      <BooleanFE
                        key={id}
                        {...otherProps}
                        variant="filled"
                        control={control}
                        rules={vRules}
                      />
                    ),
                  ],
                  [
                    R.equals("select"),
                    () => (
                      <SelectFE
                        key={id}
                        options={
                          (otherProps as Omit<SelectField<T>, "id" | "rules">)
                            .options || []
                        }
                        {...otherProps}
                        variant="filled"
                        control={control}
                        rules={vRules}
                      />
                    ),
                  ],
                ])(type)}
              </>
            );
          })}
        </Fieldset>
      ))}
    </>
  );
}
