/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router";

import { Delete, Edit } from "@mui/icons-material";
import { Button, Typography } from "@mui/material";

import { StudyMetadata } from "@/common/types";
import ConfirmationDialog from "@/components/common/dialogs/ConfirmationDialog";
import FormDialog from "@/components/common/dialogs/FormDialog";
import SelectFE from "@/components/common/fieldEditors/SelectFE";
import StringFE from "@/components/common/fieldEditors/StringFE";
import SwitchFE from "@/components/common/fieldEditors/SwitchFE";
import Fieldset from "@/components/common/Fieldset";
import { SubmitHandlerPlus } from "@/components/common/Form/types";
import {
  deleteStudyMapDistrict,
  updateStudyMapDistrict,
} from "@/redux/ducks/studyMaps";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudyMapDistrictsById } from "@/redux/selectors";

interface Props {
  open: boolean;
  onClose: () => void;
}

const defaultValues = {
  districtId: "",
  name: "",
  output: true,
  comments: "",
};

function UpdateDistrictDialog(props: Props) {
  const { open, onClose } = props;
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const dispatch = useAppDispatch();
  const districtsById = useAppSelector(getStudyMapDistrictsById);
  const [openConfirmationModal, setOpenConfirmationModal] = useState(false);

  const districtsOptions = Object.values(districtsById).map(({ name, id }) => ({
    label: name,
    value: id,
  }));

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (
    data: SubmitHandlerPlus<typeof defaultValues>,
  ) => {
    const { districtId, output, comments } = data.values;
    dispatch(
      updateStudyMapDistrict({
        studyId: study.id,
        districtId,
        output,
        comments,
      }),
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
      title={t("study.modelization.map.districts.edit")}
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
            label={t("study.modelization.map.districts")}
            variant="filled"
            options={districtsOptions}
            control={control}
            onChange={(e) => {
              setValue("name", districtsById[e.target.value as string].name);
              setValue(
                "output",
                districtsById[e.target.value as string].output,
              );
              setValue(
                "comments",
                districtsById[e.target.value as string].comments,
              );
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
            label={t("study.modelization.map.districts.field.outputs")}
            name="output"
            control={control}
            disabled={getValues("districtId") === ""}
            sx={{ ".MuiFormControlLabel-root": { m: 0 } }}
          />
          <StringFE
            label={t("study.modelization.map.districts.field.comments")}
            name="comments"
            control={control}
            fullWidth
            sx={{ mx: 0 }}
          />
          <Button
            color="error"
            variant="outlined"
            size="small"
            disabled={getValues("districtId") === ""}
            startIcon={<Delete />}
            onClick={() => setOpenConfirmationModal(true)}
            sx={{ mr: 1 }}
          >
            {t("global.delete")}
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
              <Typography sx={{ p: 3 }}>
                {t("study.modelization.map.districts.delete.confirm", {
                  0: districtsById[getValues("districtId")].name,
                })}
              </Typography>
            </ConfirmationDialog>
          )}
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default UpdateDistrictDialog;
