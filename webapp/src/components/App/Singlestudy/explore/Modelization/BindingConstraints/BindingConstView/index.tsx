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

import type { BindingConstraint } from "./utils";
import { Box, Button, Skeleton } from "@mui/material";
import Form from "../../../../../../common/Form";
import UsePromiseCond, { mergeResponses } from "../../../../../../common/utils/UsePromiseCond";
import {
  getBindingConstraint,
  getBindingConstraintList,
  updateBindingConstraint,
} from "../../../../../../../services/api/studydata";
import { useOutletContext } from "react-router";

import type { AxiosError } from "axios";
import BindingConstForm from "./BindingConstForm";
import { CommandEnum } from "../../../../Commands/Edition/commandTypes";
import ConfirmationDialog from "../../../../../../common/dialogs/ConfirmationDialog";
import ConstraintFields from "./ConstraintFields";
import Delete from "@mui/icons-material/Delete";
import type { StudyMetadata } from "../../../../../../../types/types";
import type { SubmitHandlerPlus } from "../../../../../../common/Form/types";
import { appendCommands } from "../../../../../../../services/api/variant";
import { getLinksAndClusters } from "../../../../../../../redux/selectors";
import { setCurrentBindingConst } from "../../../../../../../redux/ducks/studySyntheses";
import { t } from "i18next";
import useAppDispatch from "../../../../../../../redux/hooks/useAppDispatch";
import useEnqueueErrorSnackbar from "../../../../../../../hooks/useEnqueueErrorSnackbar";
import usePromise from "../../../../../../../hooks/usePromise";
import { useSnackbar } from "notistack";
import { useState } from "react";
import useStudySynthesis from "../../../../../../../redux/hooks/useStudySynthesis";

interface Props {
  constraintId: string;
}

// TODO rename Form (its the constraint form => properties form + terms form)
function BindingConstView({ constraintId }: Props) {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const dispatch = useAppDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [deleteConstraintDialogOpen, setDeleteConstraintDialogOpen] = useState(false);

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

  const handleSubmitConstraint = ({ values }: SubmitHandlerPlus<BindingConstraint>) => {
    const { id, name, ...updatedConstraint } = values;

    return updateBindingConstraint(study.id, constraintId, updatedConstraint);
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
          <Box sx={{ display: "flex", flexDirection: "column" }}>
            <Box sx={{ alignSelf: "flex-end" }}>
              <Button
                variant="outlined"
                startIcon={<Delete />}
                color="error"
                onClick={() => setDeleteConstraintDialogOpen(true)}
              >
                {t("global.delete.all")}
              </Button>
            </Box>
            {/* Constraint properties form */}
            <Box sx={{ display: "flex", width: 1 }}>
              <Form
                autoSubmit
                config={{ defaultValues }}
                onSubmit={handleSubmitConstraint}
                sx={{ flexGrow: 1 }}
              >
                <ConstraintFields study={study} constraintId={constraintId} />
              </Form>
            </Box>
            {/* Constraint terms form */}
            <Box sx={{ display: "flex", flexGrow: 1 }}>
              <Form autoSubmit config={{ defaultValues }} sx={{ flexGrow: 1 }}>
                <BindingConstForm
                  study={study}
                  constraintId={constraintId}
                  options={linksAndClusters}
                />
              </Form>
            </Box>
          </Box>
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
          {t("study.modelization.bindingConst.question.deleteBindingConstraint")}
        </ConfirmationDialog>
      )}
    </>
  );
}

export default BindingConstView;
