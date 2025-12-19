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

import ConfirmationDialog from "@/components/dialogs/ConfirmationDialog";
import Form from "@/components/Form";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import usePromise from "@/hooks/usePromise";
import { setCurrentBindingConst } from "@/redux/ducks/studySyntheses";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useStudySynthesis from "@/redux/hooks/useStudySynthesis";
import { getLinksAndClusters } from "@/redux/selectors";
import {
  deleteBindingConstraint,
  duplicateBindingConstraint,
  getBindingConstraint,
  getBindingConstraintList,
  updateBindingConstraint,
} from "@/services/api/studydata";
import type { StudyMetadata } from "@/types/types";
import { toError } from "@/utils/fnUtils";
import { Delete } from "@mui/icons-material";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { Button } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import semver from "semver";
import type { BindingConstraint } from "../utils";
import ConstraintFields from "./ConstraintFields";
import ConstraintTermsFields from "./ConstraintTermsFields";
import DuplicateDialog from "./DuplicateConstraintDialog";

interface Props {
  study: StudyMetadata;
  constraintId: string;
  reloadConstraintsList: VoidFunction;
}

function ConstraintForm({ study, constraintId, reloadConstraintsList }: Props) {
  const { t } = useTranslation();
  const [duplicateConstraintDialogOpen, setDuplicateConstraintDialogOpen] = useState(false);
  const [deleteConstraintDialogOpen, setDeleteConstraintDialogOpen] = useState(false);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const dispatch = useAppDispatch();

  const linksAndClusters = useStudySynthesis({
    studyId: study.id,
    selector: (state) => getLinksAndClusters(state, study.id),
  });

  const { data: existingConstraints = [] } = usePromise(async () => {
    const constraints = await getBindingConstraintList(study.id);
    return constraints.map(({ name }) => name);
  }, [study.id]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values }: SubmitHandlerPlus<BindingConstraint>) => {
    const { id, name, ...updatedConstraint } = values;

    if (semver.lt(study.version, "8.3.0")) {
      const { filterSynthesis, filterYearByYear, ...constraintWithoutFilters } = updatedConstraint;
      return updateBindingConstraint(study.id, constraintId, constraintWithoutFilters);
    } else {
      return updateBindingConstraint(study.id, constraintId, updatedConstraint);
    }
  };

  const handleDuplicate = async (newName: string) => {
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

  const handleDelete = async () => {
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
      <Form
        key={constraintId}
        config={{ defaultValues: () => getBindingConstraint(study.id, constraintId) }}
        onSubmit={handleSubmit}
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
        <ConstraintFields study={study} constraintId={constraintId} />
        <ConstraintTermsFields
          study={study}
          constraintId={constraintId}
          options={linksAndClusters.data || { links: [], clusters: [] }}
        />
      </Form>

      {duplicateConstraintDialogOpen && (
        <DuplicateDialog
          open={duplicateConstraintDialogOpen}
          onClose={() => setDuplicateConstraintDialogOpen(false)}
          constraintName={constraintId}
          existingConstraints={existingConstraints}
          onDuplicate={handleDuplicate}
        />
      )}

      {deleteConstraintDialogOpen && (
        <ConfirmationDialog
          titleIcon={Delete}
          onCancel={() => setDeleteConstraintDialogOpen(false)}
          onConfirm={handleDelete}
          alert="warning"
          open
        >
          {t("study.modeling.bindingConst.question.deleteBindingConstraint", {
            constraintName: constraintId,
          })}
        </ConfirmationDialog>
      )}
    </>
  );
}

export default ConstraintForm;
