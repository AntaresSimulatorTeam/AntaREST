import { useTranslation } from "react-i18next";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import FormDialog from "../../../../../common/dialogs/FormDialog";
import StringFE from "../../../../../common/fieldEditors/StringFE";
import { SubmitHandlerPlus } from "../../../../../common/Form/types";

interface Props {
  open: boolean;
  onClose: () => void;
  onSave: (name: string) => void;
}

function CreateAreaModal(props: Props) {
  const { open, onClose, onSave } = props;
  const [t] = useTranslation();

  const defaultValues = {
    name: "",
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<typeof defaultValues>) => {
    const { name } = data.values;

    onSave(name);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      title={t("study.modelization.map.newArea")}
      titleIcon={AddCircleIcon}
      open={open}
      onCancel={onClose}
      onSubmit={handleSubmit}
      config={{
        defaultValues,
      }}
    >
      {({ control }) => (
        <StringFE
          label={t("global.name")}
          name="name"
          control={control}
          fullWidth
          rules={{
            required: true,
            validate: (val) => val.trim().length > 0,
          }}
        />
      )}
    </FormDialog>
  );
}

export default CreateAreaModal;
