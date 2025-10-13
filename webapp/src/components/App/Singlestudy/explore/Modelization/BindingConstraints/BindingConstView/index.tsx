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

import ContentCopy from "@mui/icons-material/ContentCopy";
import DatasetIcon from "@mui/icons-material/Dataset";
import Delete from "@mui/icons-material/Delete";
import { Box, Button, Skeleton } from "@mui/material";
import { useMemo, useRef, useState } from "react";
import { FormProvider } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router";
import { toError } from "@/utils/fnUtils";
import useEnqueueErrorSnackbar from "../../../../../../../hooks/useEnqueueErrorSnackbar";
import usePromise from "../../../../../../../hooks/usePromise";
import { setCurrentBindingConst } from "../../../../../../../redux/ducks/studySyntheses";
import useAppDispatch from "../../../../../../../redux/hooks/useAppDispatch";
import useStudySynthesis from "../../../../../../../redux/hooks/useStudySynthesis";
import { getLinksAndClusters } from "../../../../../../../redux/selectors";
import {
  deleteBindingConstraint,
  duplicateBindingConstraint,
  getBindingConstraint,
  getBindingConstraintList,
  updateBindingConstraint,
} from "../../../../../../../services/api/studydata";
import type { StudyMetadata } from "../../../../../../../types/types";
import ConfirmationDialog from "../../../../../../common/dialogs/ConfirmationDialog";
import OkDialog from "../../../../../../common/dialogs/OkDialog";
import Form from "../../../../../../common/Form";
import type { SubmitHandlerPlus } from "../../../../../../common/Form/types";
import UsePromiseCond, { mergeResponses } from "../../../../../../common/utils/UsePromiseCond";
import DuplicateDialog from "../DuplicateDialog";
import BindingConstForm from "./BindingConstForm";
import ConstraintFields from "./ConstraintFields";
import ConstraintMatrix from "./Matrix";
import type { BindingConstraint } from "./utils";

interface Props {
  constraintId: string;
  reloadConstraintsList: VoidFunction;
}

// TODO rename Form (its the constraint form => properties form + terms form)
function BindingConstView({ constraintId, reloadConstraintsList }: Props) {
  const { t } = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const dispatch = useAppDispatch();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const studyVersion = Number(study.version);
  const [deleteConstraintDialogOpen, setDeleteConstraintDialogOpen] = useState(false);
  const [matrixDialogOpen, setMatrixDialogOpen] = useState(false);
  const [duplicateConstraintDialogOpen, setDuplicateConstraintDialogOpen] = useState(false);
  const [showWarningDialog, setShowWarningDialog] = useState(false);

  const dirtyFieldsRef = useRef<Partial<BindingConstraint>>({});

  const constraint = usePromise(
    () => getBindingConstraint(study.id, constraintId),
    [study.id, constraintId],
  );

  const linksAndClusters = useStudySynthesis({
    studyId: study.id,
    selector: (state) => getLinksAndClusters(state, study.id),
  });

  const constraintsList = usePromise(() => getBindingConstraintList(study.id), [study.id]);

  const existingConstraints = useMemo(
    () => constraintsList.data?.map(({ name }) => name) ?? [],
    [constraintsList.data],
  );

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleOpenMatrix = () => {
    // Prevent opening the matrix dialog if the operator field has unsaved changes.
    // The matrix API endpoint constructs the file path using the operator value
    // from the backend, so any pending changes would cause a mismatch and result
    // in an error. The user must save changes before viewing the matrix.
    if (dirtyFieldsRef.current.operator) {
      setShowWarningDialog(true);
    } else {
      setMatrixDialogOpen(true);
    }
  };

  const handleSubmit = async ({ values }: SubmitHandlerPlus<BindingConstraint>) => {
    const { id, name, ...updatedConstraint } = values;

    try {
      if (studyVersion < 830) {
        const { filterSynthesis, filterYearByYear, ...constraintWithoutFilters } =
          updatedConstraint;
        await updateBindingConstraint(study.id, constraintId, constraintWithoutFilters);
      } else {
        await updateBindingConstraint(study.id, constraintId, updatedConstraint);
      }
    } catch (error) {
      enqueueErrorSnackbar(t("study.error.updateConstraint"), toError(error));
    }
  };

  const handleDuplicateConstraint = async (newName: string) => {
    try {
      const duplicatedConstraint = await duplicateBindingConstraint(
        study.id,
        constraintId,
        newName,
      );

      reloadConstraintsList();

      if (duplicatedConstraint) {
        // Redirecting to the new duplicated constraint
        dispatch(setCurrentBindingConst(duplicatedConstraint.id));
      }
    } catch (error) {
      enqueueErrorSnackbar(t("study.error.duplicateConstraint"), toError(error));
    }
  };

  const handleDeleteConstraint = async () => {
    try {
      await deleteBindingConstraint(study.id, constraintId);

      const updatedConstraints = await getBindingConstraintList(study.id);

      reloadConstraintsList();

      if (updatedConstraints && updatedConstraints.length > 0) {
        dispatch(setCurrentBindingConst(updatedConstraints[0].id));
      }
    } catch (error) {
      enqueueErrorSnackbar(t("study.error.deleteConstraint"), toError(error));
    } finally {
      setDeleteConstraintDialogOpen(false);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <UsePromiseCond
        response={mergeResponses(constraint, linksAndClusters)}
        ifFulfilled={([defaultValues, linksAndClusters]) => (
          <Form
            config={{ defaultValues }}
            onSubmit={handleSubmit}
            enableUndoRedo
            extraActions={
              <>
                <Button
                  variant="contained"
                  color="secondary"
                  startIcon={<DatasetIcon />}
                  onClick={handleOpenMatrix}
                >
                  {t("study.modelization.bindingConst.timeSeries")}
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<ContentCopy />}
                  onClick={() => setDuplicateConstraintDialogOpen(true)}
                >
                  {t("global.duplicate")}
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Delete />}
                  color="error"
                  onClick={() => setDeleteConstraintDialogOpen(true)}
                >
                  {t("global.delete")}
                </Button>
              </>
            }
          >
            {(formApi) => {
              const { formState } = formApi;
              const { dirtyFields } = formState;

              // Keep dirtyFields ref in sync with current state
              dirtyFieldsRef.current = dirtyFields as Partial<BindingConstraint>;

              return (
                <FormProvider {...formApi}>
                  <Box sx={{ display: "flex", flexDirection: "column" }}>
                    {/* Constraint properties fields */}
                    <Box sx={{ display: "flex", width: 1 }}>
                      <ConstraintFields study={study} constraintId={constraintId} />
                    </Box>
                    {/* Constraint terms fields */}
                    <Box sx={{ display: "flex", flexGrow: 1 }}>
                      <BindingConstForm
                        study={study}
                        constraintId={constraintId}
                        options={linksAndClusters}
                      />
                    </Box>
                  </Box>
                  {/* Constraint timeseries */}
                  {matrixDialogOpen && (
                    <ConstraintMatrix
                      study={study}
                      constraintId={constraintId}
                      open={matrixDialogOpen}
                      onClose={() => setMatrixDialogOpen(false)}
                    />
                  )}
                </FormProvider>
              );
            }}
          </Form>
        )}
        ifPending={() => <Skeleton sx={{ height: 1, transform: "none" }} />}
      />

      {duplicateConstraintDialogOpen && constraint.data && (
        <DuplicateDialog
          open={duplicateConstraintDialogOpen}
          onClose={() => setDuplicateConstraintDialogOpen(false)}
          constraintName={constraint.data.name}
          existingConstraints={existingConstraints}
          onDuplicate={handleDuplicateConstraint}
        />
      )}

      {deleteConstraintDialogOpen && (
        <ConfirmationDialog
          titleIcon={Delete}
          onCancel={() => setDeleteConstraintDialogOpen(false)}
          onConfirm={handleDeleteConstraint}
          alert="warning"
          open
        >
          {t("study.modelization.bindingConst.question.deleteBindingConstraint", {
            constraintName: constraintId,
          })}
        </ConfirmationDialog>
      )}

      {showWarningDialog && (
        <OkDialog open alert="warning" maxWidth="xs" onOk={() => setShowWarningDialog(false)}>
          {t("study.configuration.general.dialogWarning")}
        </OkDialog>
      )}
    </>
  );
}

export default BindingConstView;
