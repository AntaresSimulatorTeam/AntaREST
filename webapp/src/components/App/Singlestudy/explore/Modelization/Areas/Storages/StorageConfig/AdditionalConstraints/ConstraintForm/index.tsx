/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import OkDialog from "@/components/common/dialogs/OkDialog";
import Form from "@/components/common/Form";
import type { SubmitHandlerPlus } from "@/components/common/Form/types";
import Matrix from "@/components/common/Matrix";
import {
  getAdditionalConstraint,
  updateAdditionalConstraint,
} from "@/services/api/studies/areas/storages";
import type { AdditionalConstraint } from "@/services/api/studies/areas/storages/types";
import type { StudyMetadata } from "@/types/types";
import { buildKey } from "@/utils/reactUtils";
import DatasetIcon from "@mui/icons-material/Dataset";
import DeleteIcon from "@mui/icons-material/Delete";
import { Button } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useToggle } from "react-use";
import semver from "semver";
import Fields from "./Fields";

interface Props {
  studyId: StudyMetadata["id"];
  areaId: string;
  storageId: string;
  constraintId: AdditionalConstraint["id"];
  studyVersion: StudyMetadata["version"];
  onDelete: (constraintId: AdditionalConstraint["id"]) => void;
}

function ConstraintForm({
  studyId,
  areaId,
  storageId,
  constraintId,
  studyVersion,
  onDelete,
}: Props) {
  const { t } = useTranslation();
  const [matrixDialogOpen, toggleMatrixDialogOpen] = useToggle(false);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ dirtyValues, values }: SubmitHandlerPlus<AdditionalConstraint>) => {
    const { id, name, occurrences, ...rest } = dirtyValues;

    return updateAdditionalConstraint({
      studyId,
      areaId,
      storageId,
      constraintId,
      values: occurrences ? { ...rest, occurrences: values.occurrences } : rest,
    });
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
        key={buildKey(studyId, areaId, storageId, constraintId)}
        onSubmit={handleSubmit}
        config={{
          defaultValues: () =>
            getAdditionalConstraint({
              studyId,
              areaId,
              storageId,
              constraintId,
            }),
        }}
        enableUndoRedo
        extraActions={
          <>
            <Button
              variant="contained"
              color="secondary"
              startIcon={<DatasetIcon />}
              onClick={toggleMatrixDialogOpen}
            >
              {t("global.timeSeries")}
            </Button>
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={handleDeleteClick}
            >
              {t("global.delete")}
            </Button>
          </>
        }
      >
        <Fields />
      </Form>
      {matrixDialogOpen && (
        // TODO: Prevent close when is Submitting or changing values
        <OkDialog
          open={matrixDialogOpen}
          onOk={toggleMatrixDialogOpen}
          okButtonText={t("global.close")}
          fullScreen
        >
          <Matrix
            title={t("global.timeSeries")}
            url={`input/st-storage/constraints/${areaId}/${storageId}/rhs_${constraintId}`}
            // Since v9.3 supports resize, older versions need fixed layout
            {...(semver.lt(studyVersion, "9.3.0") && {
              isTimeSeries: false,
              customColumns: ["TS 1"],
              enableFilters: true,
            })}
          />
        </OkDialog>
      )}
    </>
  );
}

export default ConstraintForm;
