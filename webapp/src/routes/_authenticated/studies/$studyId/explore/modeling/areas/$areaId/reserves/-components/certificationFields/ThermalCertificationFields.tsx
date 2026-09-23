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

import NumberFE from "@/components/fieldEditors/NumberFE";
import type { ThermalReserveCertification } from "@/services/api/studies/areas/reserves/types";
import { validateNumber } from "@/utils/validation/number";
import { useFormContext } from "react-hook-form";
import { useTranslation } from "react-i18next";

// Certification parameters of a thermal cluster. Max power must be strictly
// positive for the certification to have an effect, and the "off" max power
// can't exceed it.
function ThermalCertificationFields() {
  const { control } = useFormContext<ThermalReserveCertification>();
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <NumberFE
        label={t("study.modeling.reserves.certifications.field.participationCost")}
        name="participationCost"
        control={control}
        rules={{
          validate: validateNumber({ min: 0 }),
        }}
      />
      <NumberFE
        label={t("study.modeling.reserves.certifications.field.participationCostOff")}
        name="participationCostOff"
        control={control}
        rules={{
          validate: validateNumber({ min: 0 }),
        }}
      />
      <NumberFE
        label={t("study.modeling.reserves.certifications.field.maxPower")}
        name="maxPower"
        control={control}
        rules={{
          deps: ["maxPowerOff"],
          validate: (value) => {
            const result = validateNumber(value, { min: 0 });
            if (result !== true) {
              return result;
            }
            return value > 0 || t("form.field.mustBeGreaterThan", { 0: 0 });
          },
        }}
      />
      <NumberFE
        label={t("study.modeling.reserves.certifications.field.maxPowerOff")}
        name="maxPowerOff"
        control={control}
        rules={{
          validate: (value, { maxPower }) => validateNumber(value, { min: 0, max: maxPower }),
        }}
      />
    </>
  );
}

export default ThermalCertificationFields;
