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

import OkDialog from "@/components/dialogs/OkDialog";
import Form from "@/components/Form";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import Matrix from "@/components/Matrix";
import ViewWrapper from "@/components/page/ViewWrapper";
import useDialog from "@/hooks/useDialog";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import {
  getStorageConstraint,
  updateStorageConstraint,
} from "@/services/api/studies/areas/storages";
import type { StorageConstraint } from "@/services/api/studies/areas/storages/types";
import { unresolvedPromise } from "@/utils/promiseUtils";
import DatasetIcon from "@mui/icons-material/Dataset";
import DeleteIcon from "@mui/icons-material/Delete";
import { Button } from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { useToggle } from "react-use";
import semver from "semver";
import useDeleteStorageConstraint from "../-hooks/useDeleteStorageConstraint";
import Fields from "./-components/Fields";
import useStorageConstraint from "./-hooks/useStorageConstraint";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/additional-constraints/$constraintId/",
)({
  component: Constraint,
});

function Constraint() {
  const study = useStudy();
  const { areaId, storageId, constraintId } = Route.useParams();
  const { t } = useTranslation();
  const [matrixDialogOpen, toggleMatrixDialogOpen] = useToggle(false);
  const { confirm } = useDialog();
  const deleteConstraint = useDeleteStorageConstraint();
  const constraint = useStorageConstraint();

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ dirtyValues, values }: SubmitHandlerPlus<StorageConstraint>) => {
    const { id, name, occurrences, ...rest } = dirtyValues;

    return updateStorageConstraint({
      studyId: study.id,
      areaId,
      storageId,
      constraintId,
      values: occurrences ? { ...rest, occurrences: values.occurrences } : rest,
    });
  };

  const handleDelete = async () => {
    const isConfirmed = await confirm({
      content: t("study.modeling.storages.additionalConstraints.delete.confirm", {
        name: constraint.name,
      }),
      alert: "error",
      titleIcon: DeleteIcon,
    });

    if (isConfirmed) {
      deleteConstraint.mutate({
        studyId: study.id,
        areaId,
        storageId,
        constraintId,
      });
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ViewWrapper>
      <Form
        key={constraintId}
        onSubmit={handleSubmit}
        config={{
          defaultValues: () =>
            constraint.isOptimistic
              ? unresolvedPromise<StorageConstraint>()
              : getStorageConstraint({
                  studyId: study.id,
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
              disabled={constraint.isOptimistic}
            >
              {t("global.timeSeries")}
            </Button>
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={handleDelete}
              disabled={constraint.isOptimistic}
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
            key={constraintId}
            studyId={study.id}
            title={t("global.timeSeries")}
            url={`input/st-storage/constraints/${areaId}/${storageId}/rhs_${constraintId}`}
            // Since v9.3 supports resize, older versions need fixed layout
            {...(semver.lt(study.version, "9.3.0") && {
              isTimeSeries: false,
              customColumns: ["TS 1"],
              enableFilters: true,
            })}
          />
        </OkDialog>
      )}
    </ViewWrapper>
  );
}
