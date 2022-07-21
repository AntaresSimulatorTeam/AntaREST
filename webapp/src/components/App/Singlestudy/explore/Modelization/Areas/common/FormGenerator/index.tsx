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
import SelectFE, {
  SelectFEProps,
} from "../../../../../../../common/fieldEditors/SelectFE";
import StringFE from "../../../../../../../common/fieldEditors/StringFE";
import { StyledFieldset } from "./styles";
import {
  RegisterOptionsPlus,
  useFormContext,
} from "../../../../../../../common/Form";
import NumberFE from "../../../../../../../common/fieldEditors/NumberFE";
import SwitchFE from "../../../../../../../common/fieldEditors/SwitchFE";
import BooleanFE, {
  BooleanFEProps,
} from "../../../../../../../common/fieldEditors/BooleanFE";

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
  rules: (
    defaultValues: UnpackNestedValue<DeepPartial<T>> | undefined
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

export interface IFieldsetType<T> {
  translationId: string;
  fields: Array<IGeneratorField<T> | SelectField<T> | BooleanField<T>>;
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

export default function AutoSubmitFormGenerator<T extends FieldValues>(
  props: FormGeneratorProps<T>
) {
  const { jsonTemplate } = props;
  const formatedTemplate = jsonTemplate.map(formateFieldset);
  const [t] = useTranslation();
  const { control, defaultValues } = useFormContext<T>();

  return (
    <>
      {formatedTemplate.map((fieldset) => (
        <StyledFieldset key={fieldset.id} legend={t(fieldset.translationId)}>
          {fieldset.fields.map((field) => {
            const { id, rules, ...otherProps } = field;
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
                        rules={rules(defaultValues)}
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
                        rules={rules(defaultValues)}
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
                        rules={rules(defaultValues)}
                      />
                    ),
                  ],
                  [
                    R.equals("switch"),
                    () => (
                      <BooleanFE
                        key={id}
                        {...otherProps}
                        variant="filled"
                        control={control}
                        rules={rules(defaultValues)}
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
                        rules={rules(defaultValues)}
                      />
                    ),
                  ],
                ])(field.type)}
              </>
            );
          })}
        </StyledFieldset>
      ))}
    </>
  );
}
