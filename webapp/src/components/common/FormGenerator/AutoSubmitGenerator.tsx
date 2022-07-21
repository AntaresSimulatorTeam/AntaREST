import * as R from "ramda";
import { useMemo } from "react";
import { FieldValues } from "react-hook-form";
import FormGenerator, { IFieldsetType, IFormGenerator } from ".";

interface AutoSubmitGeneratorFormProps<T> {
  jsonTemplate: IFormGenerator<T>;
  saveField: (
    defaultValues: any,
    defaultValue: any,
    name: string,
    data: any
  ) => void;
}
export default function AutoSubmitGeneratorForm<T extends FieldValues>(
  props: AutoSubmitGeneratorFormProps<T>
) {
  const { saveField, jsonTemplate } = props;

  const formatedJsonTemplate: IFormGenerator<T> = useMemo(
    () =>
      jsonTemplate.map((fieldset) => {
        const { fields, ...otherProps } = fieldset;
        const formatedFields: IFieldsetType<T>["fields"] = fields.map(
          (field) => ({
            ...field,
            rules: (defaultValues, noDataValue) => ({
              onAutoSubmit: R.curry(saveField)(
                defaultValues,
                noDataValue,
                field.name
              ),
            }),
          })
        );

        return { fields: formatedFields, ...otherProps };
      }),
    [jsonTemplate, saveField]
  );

  return <FormGenerator jsonTemplate={formatedJsonTemplate} />;
}
