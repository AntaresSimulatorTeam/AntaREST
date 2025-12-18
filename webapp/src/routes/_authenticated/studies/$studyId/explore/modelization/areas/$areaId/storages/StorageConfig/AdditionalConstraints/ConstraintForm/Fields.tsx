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

import SelectFE from "@/components/fieldEditors/SelectFE";
import StringFE from "@/components/fieldEditors/StringFE";
import SwitchFE from "@/components/fieldEditors/SwitchFE";
import Fieldset from "@/components/Fieldset";
import { useFormContextPlus } from "@/components/Form";
import type {
  AdditionalConstraint,
  AdditionalConstraintOccurrences,
} from "@/services/api/studies/areas/storages/types";
import { Alert } from "@mui/material";
import { useTranslation } from "react-i18next";
import { OPERATOR_OPTIONS, VARIABLE_OPTIONS } from "../constants";
import OccurrencesFE from "./OccurrencesFE";
import { isOccurrencesValid } from "./utils";

function Fields() {
  const { t } = useTranslation();

  const {
    control,
    setValue,
    formState: { defaultValues },
  } = useFormContextPlus<AdditionalConstraint>();

  // Display an alert if occurrences fetch from the server are invalid
  const displayAlert = !isOccurrencesValid(defaultValues?.occurrences);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleOccurrencesChange = (newOccurrences: AdditionalConstraintOccurrences) => {
    setValue("occurrences", newOccurrences);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      {displayAlert && (
        <Alert severity="warning" sx={{ mb: 1 }}>
          {t("study.modelization.storages.additionalConstraints.occurrences.alert")}
        </Alert>
      )}
      <Fieldset legend={t("study.modelization.storages.additionalConstraints.properties")}>
        <StringFE label={t("global.name")} name="name" control={control} disabled />
        <SelectFE
          label={t("study.modelization.storages.additionalConstraints.variable")}
          name="variable"
          control={control}
          options={VARIABLE_OPTIONS}
        />
        <SelectFE
          label={t("study.modelization.storages.additionalConstraints.bounds")}
          name="operator"
          control={control}
          options={OPERATOR_OPTIONS}
        />
        <SwitchFE label={t("global.enabled")} name="enabled" control={control} />
      </Fieldset>
      <OccurrencesFE control={control} onChange={handleOccurrencesChange} />
    </>
  );
}

export default Fields;
