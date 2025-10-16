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

import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import Delete from "@mui/icons-material/Delete";
import { Box, Button, Skeleton } from "@mui/material";
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
  deleteBindingConstraint,
  duplicateBindingConstraint,
  getBindingConstraint,
  getBindingConstraintList,
  updateBindingConstraint,
} from "../../../../../../../services/api/studydata";
import type { StudyMetadata } from "../../../../../../../types/types";
import ConfirmationDialog from "../../../../../../common/dialogs/ConfirmationDialog";
import Form from "../../../../../../common/Form";
import type { SubmitHandlerPlus } from "../../../../../../common/Form/types";
import TabsView from "../../../../../../common/TabsView";
import UsePromiseCond from "../../../../../../common/utils/UsePromiseCond";
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
  const [duplicateConstraintDialogOpen, setDuplicateConstraintDialogOpen] = useState(false);
  const [currentOperator, setCurrentOperator] = useState<BindingConstraint["operator"]>();

  const constraintRes = usePromise(
    () => getBindingConstraint(study.id, constraintId),
    [study.id, constraintId],
  );

  const linksAndClusters = useStudySynthesis({
    studyId: study.id,
    selector: (state) => getLinksAndClusters(state, study.id),
  });

  const { data: existingConstraints = [] } = usePromise(async () => {
    const constraints = await getBindingConstraintList(study.id);
    return constraints.map(({ name }) => name);
  }, [study.id]);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const getDefaultValues = () => {
    return getBindingConstraint(study.id, constraintId);
  };

  const handleSubmit = ({ values }: SubmitHandlerPlus<BindingConstraint>) => {
    const { id, name, ...updatedConstraint } = values;

    if (studyVersion < 830) {
      const { filterSynthesis, filterYearByYear, ...constraintWithoutFilters } = updatedConstraint;
      return updateBindingConstraint(study.id, constraintId, constraintWithoutFilters);
    } else {
      return updateBindingConstraint(study.id, constraintId, updatedConstraint);
    }
  };

  const handleSubmitSuccessful = (
    _data: SubmitHandlerPlus<BindingConstraint>,
    submitResult: BindingConstraint,
  ) => {
    setCurrentOperator(submitResult.operator);
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
      <TabsView
        divider
        items={[
          {
            label: t("global.parameters"),
            content: (
              <Form
                key={constraintId}
                config={{ defaultValues: getDefaultValues }}
                onSubmit={handleSubmit}
                onSubmitSuccessful={handleSubmitSuccessful}
                enableUndoRedo
                extraActions={
                  <>
                    <Button
                      variant="outlined"
                      startIcon={<ContentCopyIcon />}
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
                <Box
                  sx={{
                    display: "flex",
                    flexDirection: "column",
                    height: 1,
                  }}
                >
                  {/* Constraint properties fields */}
                  <ConstraintFields study={study} constraintId={constraintId} />
                  {/* Constraint terms fields */}
                  <Box sx={{ display: "flex", flexGrow: 1 }}>
                    <BindingConstForm
                      study={study}
                      constraintId={constraintId}
                      options={linksAndClusters.data || { links: [], clusters: [] }}
                    />
                  </Box>
                </Box>
              </Form>
            ),
          },
          {
            label: t("global.timeSeries"),
            content: (
              <UsePromiseCond
                response={constraintRes}
                ifFulfilled={(constraint) => (
                  <ConstraintMatrix
                    study={study}
                    constraintId={constraintId}
                    operator={currentOperator ?? constraint.operator}
                  />
                )}
                ifPending={() => <Skeleton sx={{ height: 1, transform: "none" }} />}
              />
            ),
          },
        ]}
      />

      {duplicateConstraintDialogOpen && (
        <DuplicateDialog
          open={duplicateConstraintDialogOpen}
          onClose={() => setDuplicateConstraintDialogOpen(false)}
          constraintName={constraintId}
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
    </>
  );
}

export default BindingConstView;
