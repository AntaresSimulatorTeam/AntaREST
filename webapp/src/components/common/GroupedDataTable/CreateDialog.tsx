import { t } from "i18next";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import FormDialog from "../dialogs/FormDialog";
import StringFE from "../fieldEditors/StringFE";
import Fieldset from "../Fieldset";
import { SubmitHandlerPlus } from "../Form/types";
import SelectFE from "../fieldEditors/SelectFE";
import { nameToId } from "../../../services/utils";
import { TRow } from "./utils";
import { validateString } from "../../../utils/validationUtils";

interface Props<TData extends TRow> {
  open: boolean;
  onClose: VoidFunction;
  onSubmit: (values: TData) => Promise<void>;
  groups: string[] | readonly string[];
  existingNames: Array<TData["name"]>;
}

const defaultValues = {
  name: "",
  group: "",
};

function CreateDialog<TData extends TRow>({
  open,
  onClose,
  onSubmit,
  groups,
  existingNames,
}: Props<TData>) {
  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async ({
    values,
  }: SubmitHandlerPlus<typeof defaultValues>) => {
    await onSubmit({
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
      config={{ defaultValues }}
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

export default CreateDialog;
