import AddCircleIcon from "@mui/icons-material/AddCircle";
import FormDialog from "../dialogs/FormDialog";
import StringFE from "../fieldEditors/StringFE";
import Fieldset from "../Fieldset";
import { SubmitHandlerPlus } from "../Form/types";
import SelectFE from "../fieldEditors/SelectFE";
import type { TRow } from "./types";
import { useTranslation } from "react-i18next";

interface Props {
  open: boolean;
  onClose: VoidFunction;
  onSubmit: (values: TRow) => Promise<void>;
  groups: string[];
  existingNames: Array<TRow["name"]>;
}

function CreateDialog({
  open,
  onClose,
  onSubmit,
  groups,
  existingNames,
}: Props) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({
    values: { name, group },
  }: SubmitHandlerPlus<TRow>) => {
    return onSubmit({ name: name.trim(), group });
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
                const regex = /^[a-zA-Z0-9_\-() &]+$/;
                if (!regex.test(v.trim())) {
                  return t("form.field.specialChars", { 0: "&()_-" });
                }
                if (v.trim().length <= 0) {
                  return t("form.field.required");
                }
                if (existingNames.includes(v.trim().toLowerCase())) {
                  return t("form.field.duplicate", { 0: v });
                }
              },
            }}
            sx={{ m: 0 }}
          />
          <SelectFE
            label={t("global.group")}
            name="group"
            control={control}
            options={groups}
            rules={{ required: t("form.field.required") }}
          />
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default CreateDialog;
