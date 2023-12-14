import { useTranslation } from "react-i18next";
import ControlPointDuplicateIcon from "@mui/icons-material/ControlPointDuplicate";
import Fieldset from "../Fieldset";
import FormDialog from "../dialogs/FormDialog";
import { SubmitHandlerPlus } from "../Form/types";
import StringFE from "../fieldEditors/StringFE";

interface Props {
  open: boolean;
  onClose: VoidFunction;
  onSubmit: (name: string) => Promise<void>;
  existingNames: string[];
  defaultName: string;
}

function DuplicateDialog(props: Props) {
  const { open, onClose, onSubmit, existingNames, defaultName } = props;
  const { t } = useTranslation();
  const defaultValues = { name: defaultName };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async ({
    values: { name },
  }: SubmitHandlerPlus<typeof defaultValues>) => {
    await onSubmit(name);
    onClose();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      open={open}
      title={t("global.duplicate")}
      titleIcon={ControlPointDuplicateIcon}
      onCancel={onClose}
      onSubmit={handleSubmit}
      config={{ defaultValues }}
      isCreationForm
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
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default DuplicateDialog;
