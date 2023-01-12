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
import { getStudyMapLayers } from "../../../../../../../../redux/selectors";
import SelectFE from "../../../../../../../common/fieldEditors/SelectFE";
import Fieldset from "../../../../../../../common/Fieldset";
import ConfirmationDialog from "../../../../../../../common/dialogs/ConfirmationDialog";
import SwitchFE from "../../../../../../../common/fieldEditors/SwitchFE";

interface Props {
  open: boolean;
  onClose: () => void;
}

function EditDistrictDialog(props: Props) {
  const { open, onClose } = props;
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const layers = useAppSelector(getStudyMapLayers);
  const [openConfirmationModal, setOpenConfirmationModal] = useState(false);

  const defaultValues = {
    name: "",
    output: null,
    districtId: "",
  };

  // TODO update with districts
  const districtsOptions = Object.values(layers)
    .filter((layer) => Number(layer.id) !== 0)
    .map(({ name, id }) => ({
      label: name,
      value: id,
    }));

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (
    data: SubmitHandlerPlus<typeof defaultValues>
  ) => {
    console.log("data :>> ", data);
    console.log("study.id :>> ", study.id);
    setOpenConfirmationModal(false);
    onClose();
  };

  const handleDelete = (districtId: string) => {
    console.log("districtId", districtId);
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
            onChange={(e) =>
              setValue("name", layers[Number(e.target.value)].name)
            }
          />
          <StringFE
            label={t("global.name")}
            name="name"
            control={control}
            fullWidth
            rules={{
              required: true,
              validate: (val) => val.trim().length > 0,
            }}
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
            disabled={getValues("districtId") === ""} // TODO update to prevent District All to be deleted
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

export default EditDistrictDialog;
