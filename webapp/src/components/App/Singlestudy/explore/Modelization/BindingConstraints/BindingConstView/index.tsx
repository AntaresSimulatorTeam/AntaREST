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
import { AxiosError } from "axios";
import { t } from "i18next";
import { useSnackbar } from "notistack";
import { useOutletContext } from "react-router";

import Delete from "@mui/icons-material/Delete";
import { Box, Button, Paper, Skeleton } from "@mui/material";

import { StudyMetadata } from "@/common/types";
import { CommandEnum } from "@/components/App/Singlestudy/Commands/Edition/commandTypes";
import ConfirmationDialog from "@/components/common/dialogs/ConfirmationDialog";
import Form from "@/components/common/Form";
import { SubmitHandlerPlus } from "@/components/common/Form/types";
import UsePromiseCond, {
  mergeResponses,
} from "@/components/common/utils/UsePromiseCond";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import usePromise from "@/hooks/usePromise";
import { setCurrentBindingConst } from "@/redux/ducks/studySyntheses";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useStudySynthesis from "@/redux/hooks/useStudySynthesis";
import { getLinksAndClusters } from "@/redux/selectors";
import {
  getBindingConstraint,
  getBindingConstraintList,
  updateBindingConstraint,
} from "@/services/api/studydata";
import { appendCommands } from "@/services/api/variant";

import BindingConstForm from "./BindingConstForm";
import ConstraintFields from "./ConstraintFields";
import { BindingConstraint } from "./utils";

interface Props {
  constraintId: string;
}

// TODO rename Form (its the constraint form => properties form + terms form)
function BindingConstView({ constraintId }: Props) {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const dispatch = useAppDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [deleteConstraintDialogOpen, setDeleteConstraintDialogOpen] =
    useState(false);

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

  const handleSubmitConstraint = ({
    values,
  }: SubmitHandlerPlus<BindingConstraint>) => {
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
    <Paper
      sx={{
        p: 2,
        width: 1,
        height: 1,
        display: "flex",
        flexDirection: "column",
        overflow: "auto",
      }}
    >
      <UsePromiseCond
        response={mergeResponses(constraint, linksAndClusters)}
        ifResolved={([defaultValues, linksAndClusters]) => (
          <>
            <Box sx={{ alignSelf: "flex-end" }}>
              <Button
                variant="outlined"
                size="small"
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
          </>
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
          {t(
            "study.modelization.bindingConst.question.deleteBindingConstraint",
          )}
        </ConfirmationDialog>
      )}
    </Paper>
  );
}

export default BindingConstView;
