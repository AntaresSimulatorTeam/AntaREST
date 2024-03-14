import { useTranslation } from "react-i18next";
import ControlPointDuplicateIcon from "@mui/icons-material/ControlPointDuplicate";
import Fieldset from "../Fieldset";
import FormDialog from "../dialogs/FormDialog";
import { SubmitHandlerPlus } from "../Form/types";
import StringFE from "../fieldEditors/StringFE";
import { validateString } from "../../../utils/validationUtils";

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
              validate: (v) =>
                validateString(v, { existingValues: existingNames }),
            }}
            sx={{ m: 0 }}
          />
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default DuplicateDialog;
