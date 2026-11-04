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
import type { StorageReserveCertification } from "@/services/api/studies/areas/reserves/types";
import { validateNumber } from "@/utils/validation/number";
import { useFormContext } from "react-hook-form";
import { useTranslation } from "react-i18next";

// Certification parameters of a storage (short-term or hydro). At least one of
// max release / max store must be strictly positive for the certification to
// have an effect.
function StorageCertificationFields() {
  const { control } = useFormContext<StorageReserveCertification>();
  const { t } = useTranslation();

  const validateMaxPower = (
    value: number,
    { maxRelease, maxStore }: StorageReserveCertification,
  ) => {
    const result = validateNumber(value, { min: 0 });
    if (result !== true) {
      return result;
    }

    return (
      maxRelease > 0 ||
      maxStore > 0 ||
      t("study.modeling.reserves.certifications.field.atLeastOnePositive")
    );
  };

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
        label={t("study.modeling.reserves.certifications.field.maxRelease")}
        name="maxRelease"
        control={control}
        rules={{
          deps: ["maxStore"],
          validate: validateMaxPower,
        }}
      />
      <NumberFE
        label={t("study.modeling.reserves.certifications.field.maxStore")}
        name="maxStore"
        control={control}
        rules={{
          deps: ["maxRelease"],
          validate: validateMaxPower,
        }}
      />
    </>
  );
}

export default StorageCertificationFields;
