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

import AddCircleOutlineRoundedIcon from "@mui/icons-material/AddCircleOutlineRounded";
import { Box, Button } from "@mui/material";
import { useMemo, useState } from "react";
import { useFieldArray } from "react-hook-form";
import { useTranslation } from "react-i18next";
import type { AllClustersAndLinks, StudyMetadata } from "../../../../../../../../../types/types";
import Fieldset from "../../../../../../../../common/Fieldset";
import { useFormContextPlus } from "../../../../../../../../common/Form";
import TextSeparator from "../../../../../../../../common/TextSeparator";
import { type BindingConstraint, type ConstraintTerm, generateTermId } from "../../utils";
import ConstraintTermItem from "./ConstraintTermFE";
import AddConstraintTermDialog from "./ConstraintTermFE/AddConstraintTermDialog";

interface Props {
  study: StudyMetadata;
  constraintId: string;
  options: AllClustersAndLinks;
}

function ConstraintTermsFields({ study, options, constraintId }: Props) {
  const [t] = useTranslation();
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

  const handleUpdateTerm = (index: number, prevTerm: ConstraintTerm, newTerm: ConstraintTerm) => {
    const updatedTerm = {
      ...prevTerm,
      weight: newTerm.weight || prevTerm.weight,
      data: newTerm.data || prevTerm.data,
      offset: newTerm.offset || undefined,
    };

    update(index, updatedTerm);
  };

  const handleDeleteTerm = (termToDelete: number) => {
    remove(termToDelete);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Fieldset legend={t("study.modelization.bindingConst.constraintTerm")}>
        <Box sx={{ display: "flex", width: 1, flexDirection: "column" }}>
          <Box
            sx={{
              mb: 2,
              p: 0,
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
                deleteTerm={() => handleDeleteTerm(index)}
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
    </>
  );
}

export default ConstraintTermsFields;
