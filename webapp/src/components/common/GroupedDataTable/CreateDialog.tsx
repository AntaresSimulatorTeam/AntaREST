import AddCircleIcon from "@mui/icons-material/AddCircle";
import FormDialog from "../dialogs/FormDialog";
import StringFE from "../fieldEditors/StringFE";
import Fieldset from "../Fieldset";
import { SubmitHandlerPlus } from "../Form/types";
import SelectFE from "../fieldEditors/SelectFE";
import { validateString } from "../../../utils/validationUtils";
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
              validate: (v) =>
                validateString(v, { existingValues: existingNames }),
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
