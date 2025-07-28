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

import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import Fieldset from "@/components/common/Fieldset";
import Form from "@/components/common/Form";
import type { SubmitHandlerPlus } from "@/components/common/Form/types";
import SelectFE from "@/components/common/fieldEditors/SelectFE";
import StringFE from "@/components/common/fieldEditors/StringFE";
import SwitchFE from "@/components/common/fieldEditors/SwitchFE";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import type { StudyMetadata } from "@/types/types";
import { toError } from "@/utils/fnUtils";
import {
  type AdditionalConstraint,
  getAdditionalConstraint,
  updateAdditionalConstraint,
} from "./utils";

interface Props {
  study: StudyMetadata;
  areaId: string;
  storageId: string;
  constraint: AdditionalConstraint;
  onUpdate: () => void;
}

function ConstraintDetails({ study, areaId, storageId, constraint, onUpdate }: Props) {
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const VARIABLE_OPTIONS = [
    { value: "withdrawal", label: t("study.modelization.storages.additionalConstraints.charge") },
    { value: "injection", label: t("study.modelization.storages.additionalConstraints.discharge") },
    { value: "netting", label: t("study.modelization.storages.additionalConstraints.level") },
  ];

  const BOUNDS_OPTIONS = [
    { value: "equal", label: "=" },
    { value: "less", label: "<" },
    { value: "greater", label: ">" },
  ];

  const getDefaultValues = () => {
    return getAdditionalConstraint(study.id, areaId, storageId, constraint.id);
  };

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async ({ values }: SubmitHandlerPlus<AdditionalConstraint>) => {
    try {
      await updateAdditionalConstraint(study.id, areaId, storageId, constraint.id, values);
      onUpdate();
    } catch (error) {
      enqueueErrorSnackbar(t("global.error.create"), toError(error));
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ height: 1, display: "flex", flexDirection: "column" }}>
      <Form
        key={`${study.id}-${areaId}-${storageId}-${constraint.id}`}
        config={{ defaultValues: getDefaultValues }}
        onSubmit={handleSubmit}
        enableUndoRedo
      >
        {({ control }) => (
          <Box sx={{ mb: 2 }}>
            <Fieldset legend={t("study.modelization.storages.additionalConstraints.properties")}>
              <StringFE label={t("global.name")} name="id" control={control} size="small" />

              <SelectFE
                label={t("study.modelization.storages.additionalConstraints.variable")}
                name="variable"
                control={control}
                options={VARIABLE_OPTIONS}
                size="small"
              />

              <SelectFE
                label={t("study.modelization.storages.additionalConstraints.bounds")}
                name="operator"
                control={control}
                options={BOUNDS_OPTIONS}
                size="small"
              />

              <SwitchFE label={t("global.enabled")} name="enabled" control={control} />
            </Fieldset>
          </Box>
        )}
      </Form>
    </Box>
  );
}

export default ConstraintDetails;
