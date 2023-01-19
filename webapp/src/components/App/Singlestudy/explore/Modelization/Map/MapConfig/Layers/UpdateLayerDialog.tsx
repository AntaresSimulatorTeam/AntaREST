import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router";
import { Delete, Edit } from "@mui/icons-material";
import { Button, Typography } from "@mui/material";
import { useMemo, useState } from "react";
import FormDialog from "../../../../../../../common/dialogs/FormDialog";
import StringFE from "../../../../../../../common/fieldEditors/StringFE";
import { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import { StudyMetadata } from "../../../../../../../../common/types";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { getStudyMapLayersById } from "../../../../../../../../redux/selectors";
import SelectFE from "../../../../../../../common/fieldEditors/SelectFE";
import Fieldset from "../../../../../../../common/Fieldset";
import ConfirmationDialog from "../../../../../../../common/dialogs/ConfirmationDialog";
import {
  deleteStudyMapLayer,
  updateStudyMapLayer,
} from "../../../../../../../../redux/ducks/studyMaps";
import useAppDispatch from "../../../../../../../../redux/hooks/useAppDispatch";

interface Props {
  open: boolean;
  onClose: () => void;
}

const defaultValues = {
  name: "",
  layerId: "",
};

function UpdateLayerDialog(props: Props) {
  const { open, onClose } = props;
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const dispatch = useAppDispatch();
  const layersById = useAppSelector(getStudyMapLayersById);
  const [openConfirmationModal, setOpenConfirmationModal] = useState(false);

  const layersOptions = Object.values(layersById)
    .filter((layer) => layer.id !== "0")
    .map(({ name, id }) => ({
      label: name,
      value: id,
    }));

  const existingLayers = useMemo(
    () => Object.values(layersById).map((layer) => layer.name.toLowerCase()),
    [layersById]
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (
    data: SubmitHandlerPlus<typeof defaultValues>
  ) => {
    const { layerId, name } = data.values;
    if (layerId && name) {
      return dispatch(updateStudyMapLayer({ studyId: study.id, layerId, name }))
        .unwrap()
        .then(onClose);
    }
  };

  const handleDelete = async (layerId: string) => {
    if (layerId) {
      dispatch(deleteStudyMapLayer({ studyId: study.id, layerId }));
    }
    setOpenConfirmationModal(false);
    onClose();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      title="Edit Layers"
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
            name="layerId"
            label={t("Layers")}
            variant="filled"
            options={layersOptions}
            control={control}
            onChange={(e) =>
              setValue("name", layersById[String(e.target.value)].name)
            }
          />
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
                if (existingLayers.includes(v.toLowerCase())) {
                  return `The Layer "${v}" already exists`;
                }
              },
            }}
            disabled={getValues("layerId") === ""}
            sx={{ mx: 0 }}
          />
          <Button
            color="error"
            variant="outlined"
            size="small"
            startIcon={<Delete />}
            disabled={getValues("layerId") === ""}
            onClick={() => setOpenConfirmationModal(true)}
            sx={{ mr: 1 }}
          >
            Delete Layer
          </Button>
          {openConfirmationModal && (
            <ConfirmationDialog
              onCancel={() => setOpenConfirmationModal(false)}
              onConfirm={(): void => {
                handleDelete(getValues("layerId"));
              }}
              alert="warning"
              open
            >
              <Typography sx={{ p: 3 }}>Delete layer ?</Typography>
            </ConfirmationDialog>
          )}
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default UpdateLayerDialog;
