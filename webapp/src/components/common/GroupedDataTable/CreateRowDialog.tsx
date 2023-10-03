import { t } from "i18next";
import { v4 as uuidv4 } from "uuid";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import FormDialog from "../dialogs/FormDialog";
import StringFE from "../fieldEditors/StringFE";
import Fieldset from "../Fieldset";
import { SubmitHandlerPlus } from "../Form/types";
import SelectFE from "../fieldEditors/SelectFE";
import { TRow } from ".";

interface Props<TData extends TRow> {
  open: boolean;
  onClose: VoidFunction;
  onSubmit: (values: TData) => void;
  groups: string[];
  existingNames: Array<TData["name"]>;
}

const defaultValues = {
  name: "",
  group: "",
};

function CreateRowDialog<TData extends TRow>({
  open,
  onClose,
  onSubmit,
  groups,
  existingNames,
}: Props<TData>) {
  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({
    values,
  }: SubmitHandlerPlus<typeof defaultValues>) => {
    onSubmit({ ...values, id: uuidv4(), name: values.name.trim() } as TData);
    onClose();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      title={t("button.add")}
      titleIcon={AddCircleIcon}
      open={open}
      onCancel={onClose}
      onSubmit={handleSubmit}
      config={{
        defaultValues,
      }}
    >
      {({ control }) => (
        <Fieldset fullFieldWidth>
          <StringFE
            label={t("global.name")}
            name="name"
            control={control}
            fullWidth
            rules={{
              required: { value: true, message: t("form.field.required") },
              validate: (v) => {
                if (v.trim().length <= 0) {
                  return t("form.field.required");
                }
                if (existingNames.includes(v.trim())) {
                  return t("form.field.duplicate", { 0: v });
                }
              },
            }}
            sx={{ m: 0 }}
          />
          <SelectFE
            label={t("study.modelization.clusters.group")}
            name="group"
            control={control}
            options={groups}
            sx={{
              alignSelf: "center",
            }}
          />
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default CreateRowDialog;
