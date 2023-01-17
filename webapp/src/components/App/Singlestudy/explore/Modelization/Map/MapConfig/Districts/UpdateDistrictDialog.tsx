import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router";
import { Delete, Edit } from "@mui/icons-material";
import { Button, Typography } from "@mui/material";
import { useState } from "react";
import FormDialog from "../../../../../../../common/dialogs/FormDialog";
import StringFE from "../../../../../../../common/fieldEditors/StringFE";
import { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import { StudyMetadata } from "../../../../../../../../common/types";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { getStudyMapDistricts } from "../../../../../../../../redux/selectors";
import SelectFE from "../../../../../../../common/fieldEditors/SelectFE";
import Fieldset from "../../../../../../../common/Fieldset";
import ConfirmationDialog from "../../../../../../../common/dialogs/ConfirmationDialog";
import SwitchFE from "../../../../../../../common/fieldEditors/SwitchFE";
import useAppDispatch from "../../../../../../../../redux/hooks/useAppDispatch";
import {
  deleteStudyMapDistrict,
  updateStudyMapDistrict,
} from "../../../../../../../../redux/ducks/studyMaps";

interface Props {
  open: boolean;
  onClose: () => void;
}

const defaultValues = {
  name: "",
  output: true,
  districtId: "",
};

function UpdateDistrictDialog(props: Props) {
  const { open, onClose } = props;
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const dispatch = useAppDispatch();
  const districts = useAppSelector(getStudyMapDistricts);
  const [openConfirmationModal, setOpenConfirmationModal] = useState(false);

  const districtsOptions = Object.values(districts).map(({ name, id }) => ({
    label: name,
    value: id,
  }));

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (
    data: SubmitHandlerPlus<typeof defaultValues>
  ) => {
    const { districtId, output } = data.values;
    dispatch(
      updateStudyMapDistrict({
        studyId: study.id,
        districtId,
        output,
      })
    );
    onClose();
  };

  const handleDelete = (districtId: string) => {
    if (districtId) {
      dispatch(deleteStudyMapDistrict({ studyId: study.id, districtId }));
    }
    setOpenConfirmationModal(false);
    onClose();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      title="Edit District"
      titleIcon={Edit}
      open={open}
      onCancel={onClose}
      onSubmit={handleSubmit}
      config={{
        defaultValues,
      }}
    >
      {({ control, setValue, getValues }) => (
        <Fieldset fullFieldWidth>
          <SelectFE
            name="districtId"
            label={t("Districts")}
            variant="filled"
            options={districtsOptions}
            control={control}
            onChange={(e) => {
              setValue("name", districts[e.target.value as string].name);
            }}
          />
          <StringFE
            label={t("global.name")}
            name="name"
            control={control}
            fullWidth
            disabled
            sx={{ mx: 0 }}
          />
          <SwitchFE
            name="output"
            label="Output"
            control={control}
            sx={{ ".MuiFormControlLabel-root": { m: 0 } }}
          />
          <Button
            color="error"
            variant="outlined"
            size="small"
            startIcon={<Delete />}
            onClick={() => setOpenConfirmationModal(true)}
            sx={{ mr: 1 }}
          >
            Delete District
          </Button>
          {openConfirmationModal && (
            <ConfirmationDialog
              onCancel={() => setOpenConfirmationModal(false)}
              onConfirm={(): void => {
                handleDelete(getValues("districtId"));
              }}
              alert="warning"
              open
            >
              <Typography sx={{ p: 3 }}>Delete district ?</Typography>
            </ConfirmationDialog>
          )}
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default UpdateDistrictDialog;
