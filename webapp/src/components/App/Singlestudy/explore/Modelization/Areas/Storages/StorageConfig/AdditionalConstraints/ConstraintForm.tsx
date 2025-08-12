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

import DatasetIcon from "@mui/icons-material/Dataset";
import DeleteIcon from "@mui/icons-material/Delete";
import { Button } from "@mui/material";
import * as R from "ramda";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import OkDialog from "@/components/common/dialogs/OkDialog";
import Fieldset from "@/components/common/Fieldset";
import Form from "@/components/common/Form";
import type { SubmitHandlerPlus } from "@/components/common/Form/types";
import SelectFE from "@/components/common/fieldEditors/SelectFE";
import StringFE from "@/components/common/fieldEditors/StringFE";
import SwitchFE from "@/components/common/fieldEditors/SwitchFE";
import Matrix from "@/components/common/Matrix";
import {
  getAdditionalConstraint,
  updateAdditionalConstraints,
} from "@/services/api/studies/areas/storages";
import type { AdditionalConstraint } from "@/services/api/studies/areas/storages/types";
import { OPERATOR_OPTIONS, VARIABLE_OPTIONS } from "./constants";

interface Props {
  studyId: string;
  areaId: string;
  storageId: string;
  constraintId: AdditionalConstraint["id"];
  studyVersion: number;
  onDelete: (constraintId: AdditionalConstraint["id"]) => void;
}

const pickFieldValues = R.pick(["name", "variable", "operator", "enabled"]);

function ConstraintForm({
  studyId,
  areaId,
  storageId,
  constraintId,
  studyVersion,
  onDelete,
}: Props) {
  const { t } = useTranslation();
  const [matrixDialogOpen, setMatrixDialogOpen] = useState(false);

  ////////////////////////////////////////////////////////////////
  // Functions
  ////////////////////////////////////////////////////////////////

  const getDefaultValues = async () => {
    const constraint = await getAdditionalConstraint({
      studyId,
      areaId,
      storageId,
      constraintId,
    });

    return pickFieldValues(constraint);
  };

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  type FieldValues = Awaited<ReturnType<typeof getDefaultValues>>;

  const handleSubmit = async ({ dirtyValues }: SubmitHandlerPlus<FieldValues>) => {
    const { name, ...newValues } = dirtyValues;

    const updatedConstraints = await updateAdditionalConstraints({
      studyId,
      areaId,
      storageId,
      constraints: {
        [constraintId]: newValues,
      },
    });

    return pickFieldValues(updatedConstraints[0]);
  };

  const handleDeleteClick = () => {
    onDelete(constraintId);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Form
        key={`${studyId}-${areaId}-${storageId}-${constraintId}`}
        onSubmit={handleSubmit}
        config={{ defaultValues: getDefaultValues }}
        enableUndoRedo
        extraActions={
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={handleDeleteClick}
          >
            {t("global.delete")}
          </Button>
        }
      >
        {({ control }) => (
          <>
            <Fieldset legend={t("study.modelization.storages.additionalConstraints.properties")}>
              <StringFE
                label={t("global.name")}
                name="name"
                control={control}
                size="small"
                disabled
              />
              <SelectFE
                label={t("study.modelization.storages.additionalConstraints.variable")}
                name="variable"
                control={control}
                options={VARIABLE_OPTIONS}
              />
              <SelectFE
                label={t("study.modelization.storages.additionalConstraints.bounds")}
                name="operator"
                control={control}
                options={OPERATOR_OPTIONS}
              />
              <SwitchFE label={t("global.enabled")} name="enabled" control={control} />
            </Fieldset>
            <Button
              variant="contained"
              color="secondary"
              startIcon={<DatasetIcon />}
              onClick={() => setMatrixDialogOpen(true)}
            >
              {t("global.timeSeries")}
            </Button>
          </>
        )}
      </Form>

      {matrixDialogOpen && (
        <OkDialog
          open={matrixDialogOpen}
          onOk={() => setMatrixDialogOpen(false)}
          fullScreen
          sx={{ m: 3 }}
        >
          <Matrix
            title={t("global.timeSeries")}
            url={`input/st-storage/constraints/${areaId}/${storageId}/rhs_${constraintId}`}
            // Since v9.3 supports resize, older versions need fixed layout
            {...(studyVersion < 930 && {
              isTimeSeries: false,
              customColumns: ["TS 1"],
            })}
          />
        </OkDialog>
      )}
    </>
  );
}

export default ConstraintForm;
