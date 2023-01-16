import { useTranslation } from "react-i18next";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import { useOutletContext } from "react-router";
import FormDialog from "../../../../../../../common/dialogs/FormDialog";
import StringFE from "../../../../../../../common/fieldEditors/StringFE";
import { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import { StudyMetadata } from "../../../../../../../../common/types";
import SwitchFE from "../../../../../../../common/fieldEditors/SwitchFE";
import Fieldset from "../../../../../../../common/Fieldset";
import useAppDispatch from "../../../../../../../../redux/hooks/useAppDispatch";
import { createStudyMapDistrict } from "../../../../../../../../redux/ducks/studyMaps";

interface Props {
  open: boolean;
  onClose: () => void;
}

function CreateDistrictDialog(props: Props) {
  const { open, onClose } = props;
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const dispatch = useAppDispatch();

  const defaultValues = {
    name: "",
    output: true,
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<typeof defaultValues>) => {
    const { name, output } = data.values;
    dispatch(
      createStudyMapDistrict({
        studyId: study.id,
        name,
        output,
      })
    );
    onClose();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      title="Add new district"
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
              required: true,
              validate: (val) => val.trim().length > 0,
            }}
            sx={{ m: 0 }}
          />
          <SwitchFE
            name="output"
            label="Output"
            control={control}
            sx={{ ".MuiFormControlLabel-root": { m: 0 } }}
          />
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default CreateDistrictDialog;
