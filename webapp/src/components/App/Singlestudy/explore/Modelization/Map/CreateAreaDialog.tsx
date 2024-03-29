import { useTranslation } from "react-i18next";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import FormDialog from "../../../../../common/dialogs/FormDialog";
import StringFE from "../../../../../common/fieldEditors/StringFE";
import { SubmitHandlerPlus } from "../../../../../common/Form/types";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getAreas } from "../../../../../../redux/selectors";
import { validateString } from "../../../../../../utils/validationUtils";

interface Props {
  studyId: string;
  open: boolean;
  onClose: () => void;
  createArea: (name: string) => void;
}

function CreateAreaDialog(props: Props) {
  const { studyId, open, onClose, createArea } = props;
  const [t] = useTranslation();
  const existingAreas = useAppSelector((state) =>
    getAreas(state, studyId).map((area) => area.name),
  );

  const defaultValues = {
    name: "",
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<typeof defaultValues>) => {
    return createArea(data.values.name.trim());
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
            validate: (v) =>
              validateString(v, { existingValues: existingAreas }),
          }}
        />
      )}
    </FormDialog>
  );
}

export default CreateAreaDialog;
