import { t } from "i18next";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import FormDialog from "../dialogs/FormDialog";
import StringFE from "../fieldEditors/StringFE";
import Fieldset from "../Fieldset";
import { SubmitHandlerPlus } from "../Form/types";
import SelectFE from "../fieldEditors/SelectFE";
import { TRow } from ".";
import { nameToId } from "../../../services/utils";

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
    onSubmit({
      ...values,
      id: nameToId(values.name),
      name: values.name.trim(),
    } as TData);
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
                const regex = /[^a-zA-Z0-9_\-(),& ]+$/;
                if (regex.test(v.trim())) {
                  return t("form.field.specialChars", ["&()_,-"]);
                }
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
            required
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
