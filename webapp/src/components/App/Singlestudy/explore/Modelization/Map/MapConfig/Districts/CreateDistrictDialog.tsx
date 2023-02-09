import { useTranslation } from "react-i18next";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import { useOutletContext } from "react-router";
import { useMemo } from "react";
import FormDialog from "../../../../../../../common/dialogs/FormDialog";
import StringFE from "../../../../../../../common/fieldEditors/StringFE";
import { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import { StudyMetadata } from "../../../../../../../../common/types";
import SwitchFE from "../../../../../../../common/fieldEditors/SwitchFE";
import Fieldset from "../../../../../../../common/Fieldset";
import useAppDispatch from "../../../../../../../../redux/hooks/useAppDispatch";
import { createStudyMapDistrict } from "../../../../../../../../redux/ducks/studyMaps";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { getStudyMapDistrictsById } from "../../../../../../../../redux/selectors";

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
  const [t] = useTranslation();
  const dispatch = useAppDispatch();
  const districtsById = useAppSelector(getStudyMapDistrictsById);

  const existingDistricts = useMemo(
    () =>
      Object.values(districtsById).map((district) =>
        district.name.toLowerCase()
      ),
    [districtsById]
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<typeof defaultValues>) => {
    const { name, output, comments } = data.values;

    return dispatch(
      createStudyMapDistrict({
        studyId: study.id,
        name,
        output,
        comments,
      })
    )
      .unwrap()
      .then(onClose);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      title={t("study.modelization.map.districts.add")}
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
                if (v.trim().length <= 0) {
                  return false;
                }
                if (existingDistricts.includes(v.toLowerCase())) {
                  return `The District "${v}" already exists`;
                }
              },
            }}
            sx={{ m: 0 }}
          />
          <SwitchFE
            name="output"
            label={t("study.modelization.map.districts.field.outputs")}
            control={control}
            sx={{ ".MuiFormControlLabel-root": { m: 0 } }}
          />
          <StringFE
            name="comments"
            label={t("study.modelization.map.districts.field.comments")}
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
