import { useTranslation } from "react-i18next";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import { useOutletContext } from "react-router";
import { AxiosError } from "axios";
import FormDialog from "../../../../../../../common/dialogs/FormDialog";
import StringFE from "../../../../../../../common/fieldEditors/StringFE";
import { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import { StudyMetadata } from "../../../../../../../../common/types";
import SwitchFE from "../../../../../../../common/fieldEditors/SwitchFE";
import Fieldset from "../../../../../../../common/Fieldset";
import useAppDispatch from "../../../../../../../../redux/hooks/useAppDispatch";
import { createStudyMapDistrict } from "../../../../../../../../redux/ducks/studyMaps";
import useEnqueueErrorSnackbar from "../../../../../../../../hooks/useEnqueueErrorSnackbar";

interface Props {
  open: boolean;
  onClose: () => void;
}

const defaultValues = {
  name: "",
  output: true,
  comments: "",
};

function CreateDistrictDialog(props: Props) {
  const { open, onClose } = props;
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const dispatch = useAppDispatch();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<typeof defaultValues>) => {
    const { name, output, comments } = data.values;
    try {
      dispatch(
        createStudyMapDistrict({
          studyId: study.id,
          name,
          output,
          comments,
        })
      );
    } catch (e) {
      enqueueErrorSnackbar(t("study.error.createDistrict"), e as AxiosError);
    }

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
          <StringFE
            name="comments"
            label="Comments"
            control={control}
            fullWidth
            sx={{ m: 0 }}
          />
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default CreateDistrictDialog;
