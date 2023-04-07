import * as R from "ramda";
import * as RA from "ramda-adjunct";
import { v4 as uuidv4 } from "uuid";
import { FieldValues, FormState, Path } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { SxProps, Theme } from "@mui/material";
import { Fragment, ReactNode, useMemo } from "react";
import SelectFE, { SelectFEProps } from "../fieldEditors/SelectFE";
import StringFE from "../fieldEditors/StringFE";
import Fieldset from "../Fieldset";
import { useFormContextPlus } from "../Form";
import NumberFE from "../fieldEditors/NumberFE";
import SwitchFE from "../fieldEditors/SwitchFE";
import BooleanFE, { BooleanFEProps } from "../fieldEditors/BooleanFE";
import { RegisterOptionsPlus } from "../Form/types";

export type GeneratorFieldType =
  | "text"
  | "number"
  | "select"
  | "switch"
  | "boolean";

export interface IGeneratorField<T extends FieldValues> {
  type: GeneratorFieldType;
  name: Path<T> & (string | undefined);
  label: string;
  path: string;
  sx?: SxProps<Theme> | undefined;
  required?: boolean | string;
  rules?: (
    name: IGeneratorField<T>["name"],
    path: string,
    required?: boolean | string,
    defaultValues?: FormState<T>["defaultValues"]
  ) =>
    | Omit<
        RegisterOptionsPlus<T, Path<T> & (string | undefined)>,
        "disabled" | "valueAsNumber" | "valueAsDate" | "setValueAs"
      >
    | undefined;
}

export interface SelectField<T extends FieldValues> extends IGeneratorField<T> {
  options: SelectFEProps["options"];
}

export interface BooleanField<T extends FieldValues>
  extends IGeneratorField<T> {
  falseText: BooleanFEProps["falseText"];
  trueText: BooleanFEProps["trueText"];
}

export type IGeneratorFieldType<T extends FieldValues> =
  | IGeneratorField<T>
  | SelectField<T>
  | BooleanField<T>;

export interface IFieldsetType<T extends FieldValues> {
  legend: string | ReactNode;
  fields: Array<IGeneratorFieldType<T>>;
}

export type IFormGenerator<T extends FieldValues> = Array<IFieldsetType<T>>;

export interface FormGeneratorProps<T extends FieldValues> {
  jsonTemplate: IFormGenerator<T>;
}

function formateFieldset<T extends FieldValues>(fieldset: IFieldsetType<T>) {
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
  const {
    control,
    formState: { defaultValues },
  } = useFormContextPlus<T>();

  return (
    <>
      {formatedTemplate.map((fieldset) => (
        <Fieldset
          key={fieldset.id}
          legend={
            RA.isString(fieldset.legend) ? t(fieldset.legend) : fieldset.legend
          }
        >
          {fieldset.fields.map((field) => {
            const { id, path, rules, type, required, ...otherProps } = field;
            const vRules = rules
              ? rules(field.name, path, required, defaultValues)
              : undefined;
            return (
              <Fragment key={id}>
                {R.cond([
                  [
                    R.equals("text"),
                    () => (
                      <StringFE
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
              </Fragment>
            );
          })}
        </Fieldset>
      ))}
    </>
  );
}
