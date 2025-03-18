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

import type { AxiosError } from "axios";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Box, Button } from "@mui/material";
import AddCircleOutlineRoundedIcon from "@mui/icons-material/AddCircleOutlineRounded";
import DeleteIcon from "@mui/icons-material/Delete";
import { useFieldArray } from "react-hook-form";
import { useSnackbar } from "notistack";
import useEnqueueErrorSnackbar from "../../../../../../../hooks/useEnqueueErrorSnackbar";
import { generateTermId, type ConstraintTerm, type BindingConstraint } from "./utils";
import type { AllClustersAndLinks, StudyMetadata } from "../../../../../../../types/types";
import ConstraintTermItem from "./ConstraintTerm";
import { useFormContextPlus } from "../../../../../../common/Form";
import {
  deleteConstraintTerm,
  updateConstraintTerm,
} from "../../../../../../../services/api/studydata";
import TextSeparator from "../../../../../../common/TextSeparator";
import AddConstraintTermDialog from "./AddConstraintTermDialog";
import ConfirmationDialog from "../../../../../../common/dialogs/ConfirmationDialog";
import useDebounce from "../../../../../../../hooks/useDebounce";
import Fieldset from "../../../../../../common/Fieldset";

interface Props {
  study: StudyMetadata;
  constraintId: string;
  options: AllClustersAndLinks;
}

// TODO rename ConstraintTermsFields
function BindingConstForm({ study, options, constraintId }: Props) {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [termToDelete, setTermToDelete] = useState<number>();
  const [openConstraintTermDialog, setOpenConstraintTermDialog] = useState(false);

  const { control } = useFormContextPlus<BindingConstraint>();

  const { fields, update, append, remove } = useFieldArray({
    control,
    name: "terms",
  });

  const constraintTerms = useMemo(
    () => fields.map((term) => ({ ...term, id: generateTermId(term.data) })),
    [fields],
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleUpdateTerm = useDebounce(
    async (index: number, prevTerm: ConstraintTerm, newTerm: ConstraintTerm) => {
      try {
        const updatedTerm = {
          ...prevTerm,
          weight: newTerm.weight || prevTerm.weight,
          data: newTerm.data || prevTerm.data,
          offset: newTerm.offset || undefined,
        };

        await updateConstraintTerm(study.id, constraintId, updatedTerm);

        update(index, updatedTerm);

        enqueueSnackbar(t("global.update.success"), {
          variant: "success",
        });
      } catch (error) {
        enqueueErrorSnackbar(t("study.error.updateConstraintTerm"), error as AxiosError);
      }
    },
    500,
  );

  const handleDeleteTerm = async (termToDelete: number) => {
    try {
      const termId = generateTermId(constraintTerms[termToDelete].data);
      await deleteConstraintTerm(study.id, constraintId, termId);
      remove(termToDelete);
    } catch (error) {
      enqueueErrorSnackbar(t("study.error.deleteConstraintTerm"), error as AxiosError);
    } finally {
      setTermToDelete(undefined);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Fieldset legend={t("study.modelization.bindingConst.constraintTerm")} sx={{ py: 2 }}>
        <Box sx={{ display: "flex", width: 1, flexDirection: "column" }}>
          <Box
            sx={{
              mb: 2,
            }}
          >
            <Button
              variant="contained"
              color="primary"
              startIcon={<AddCircleOutlineRoundedIcon />}
              onClick={() => setOpenConstraintTermDialog(true)}
            >
              {t("study.modelization.bindingConst.createConstraintTerm")}
            </Button>
          </Box>
          {constraintTerms.map((term: ConstraintTerm, index: number) => (
            <Box key={term.id}>
              {index > 0 && <TextSeparator text="+" textStyle={{ fontSize: "16px" }} />}
              <ConstraintTermItem
                options={options}
                saveValue={(newTerm) => handleUpdateTerm(index, term, newTerm)}
                term={term}
                deleteTerm={() => setTermToDelete(index)}
                constraintTerms={constraintTerms}
              />
            </Box>
          ))}
        </Box>
      </Fieldset>

      {openConstraintTermDialog && (
        <AddConstraintTermDialog
          open={openConstraintTermDialog}
          studyId={study.id}
          constraintId={constraintId}
          title={t("study.modelization.bindingConst.createConstraintTerm")}
          onCancel={() => setOpenConstraintTermDialog(false)}
          append={append}
          constraintTerms={constraintTerms}
          options={options}
        />
      )}

      {termToDelete !== undefined && (
        <ConfirmationDialog
          titleIcon={DeleteIcon}
          onCancel={() => setTermToDelete(undefined)}
          onConfirm={() => handleDeleteTerm(termToDelete)}
          alert="warning"
          open
        >
          {t("study.modelization.bindingConst.question.deleteConstraintTerm")}
        </ConfirmationDialog>
      )}
    </>
  );
}

export default BindingConstForm;
