/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import { Button, Typography } from "@mui/material";
import { useMemo, useState } from "react";
import FormDialog from "../../../../../../../common/dialogs/FormDialog";
import StringFE from "../../../../../../../common/fieldEditors/StringFE";
import type { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import type { StudyMetadata } from "../../../../../../../../types/types";
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
import { validateString } from "@/utils/validation/string";

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
    () => Object.values(layersById).map(({ name }) => name),
    [layersById],
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (data: SubmitHandlerPlus<typeof defaultValues>) => {
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
      title={t("study.modelization.map.layers.edit")}
      titleIcon={EditIcon}
      open={open}
      onCancel={onClose}
      onSubmit={handleSubmit}
      config={{
        defaultValues,
      }}
    >
      {({ control, getValues, reset }) => (
        <Fieldset fullFieldWidth>
          <SelectFE
            name="layerId"
            label={t("Layers")}
            options={layersOptions}
            control={control}
            onChange={({ target: { value } }) => {
              reset({
                layerId: value as string,
                name: layersById[value as string].name,
              });
            }}
          />
          <StringFE
            label={t("global.name")}
            name="name"
            control={control}
            fullWidth
            rules={{
              validate: (v) =>
                validateString(v, {
                  existingValues: existingLayers,
                  // Excludes the current layer's original name to allow edits without false duplicates.
                  editedValue: layersById[getValues("layerId")].name,
                }),
            }}
            disabled={getValues("layerId") === ""}
            sx={{ mx: 0 }}
          />
          <Button
            color="error"
            variant="outlined"
            startIcon={<DeleteIcon />}
            disabled={getValues("layerId") === ""}
            onClick={() => setOpenConfirmationModal(true)}
            sx={{ mr: 1 }}
          >
            {t("global.delete")}
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
              <Typography sx={{ p: 3 }}>
                {t("study.modelization.map.layers.delete.confirm", {
                  0: layersById[getValues("layerId")].name,
                })}
              </Typography>
            </ConfirmationDialog>
          )}
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default UpdateLayerDialog;
