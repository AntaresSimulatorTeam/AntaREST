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
import Delete from "@mui/icons-material/Delete";
import { Box, Button, Skeleton } from "@mui/material";
import type { AxiosError } from "axios";
import { useSnackbar } from "notistack";
import { useState } from "react";
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
  getBindingConstraint,
  getBindingConstraintList,
  updateBindingConstraint,
} from "../../../../../../../services/api/studydata";
import { appendCommands } from "../../../../../../../services/api/variant";
import type { StudyMetadata } from "../../../../../../../types/types";
import ConfirmationDialog from "../../../../../../common/dialogs/ConfirmationDialog";
import Form from "../../../../../../common/Form";
import type { SubmitHandlerPlus } from "../../../../../../common/Form/types";
import UsePromiseCond, { mergeResponses } from "../../../../../../common/utils/UsePromiseCond";
import { CommandEnum } from "../../../../CommandsDrawer/EditionView/commandTypes";
import BindingConstForm from "./BindingConstForm";
import ConstraintFields from "./ConstraintFields";
import ConstraintMatrix from "./Matrix";
import type { BindingConstraint } from "./utils";

interface Props {
  constraintId: string;
}

// TODO rename Form (its the constraint form => properties form + terms form)
function BindingConstView({ constraintId }: Props) {
  const { t } = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const dispatch = useAppDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const studyVersion = Number(study.version);
  const [deleteConstraintDialogOpen, setDeleteConstraintDialogOpen] = useState(false);
  const [matrixDialogOpen, setMatrixDialogOpen] = useState(false);

  const constraint = usePromise(
    () => getBindingConstraint(study.id, constraintId),
    [study.id, constraintId],
  );

  const linksAndClusters = useStudySynthesis({
    studyId: study.id,
    selector: (state) => getLinksAndClusters(state, study.id),
  });

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

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

  /**
   * @deprecated
   * We should use a dedicated DELETE endpoint for removing binding constraints. This endpoint is
   * not currently exposed by the API, but it is recommended to transition to it once available.
   *
   * This function sends a commandto remove the binding constraint by its ID.
   * After successful deletion, it triggers a UI update to reflect the removal.
   */
  const handleDeleteConstraint = async () => {
    try {
      await appendCommands(study.id, [
        {
          action: CommandEnum.REMOVE_BINDING_CONSTRAINT,
          args: {
            id: constraintId,
          },
        },
      ]);

      const updatedConstraints = await getBindingConstraintList(study.id);

      if (updatedConstraints && updatedConstraints.length > 0) {
        // Trigger a reload redirecting to the first constraint
        dispatch(setCurrentBindingConst(updatedConstraints[0].id));
      }

      enqueueSnackbar(t("study.success.deleteConstraint"), {
        variant: "success",
      });
    } catch (e) {
      enqueueErrorSnackbar(t("study.error.deleteConstraint"), e as AxiosError);
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
            extraActions={
              <>
                <Button
                  variant="contained"
                  color="secondary"
                  startIcon={<DatasetIcon />}
                  onClick={() => setMatrixDialogOpen(true)}
                >
                  {t("study.modelization.bindingConst.timeSeries")}
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
          </Form>
        )}
        ifPending={() => <Skeleton sx={{ height: 1, transform: "none" }} />}
      />

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
    </>
  );
}

export default BindingConstView;
