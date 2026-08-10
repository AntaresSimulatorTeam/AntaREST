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

import FormDrawer from "@/components/FormDrawer";
import NumberFE from "@/components/fieldEditors/NumberFE";
import Fieldset from "@/components/Fieldset";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import type { ReserveCertification } from "@/services/api/studies/areas/reserves/types";
import { validateNumber } from "@/utils/validation/number";
import EditIcon from "@mui/icons-material/Edit";
import { Chip, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

interface Props {
  open: boolean;
  clusterName: string;
  clusterEnabled: boolean;
  certification: ReserveCertification;
  onClose: VoidFunction;
  onSubmit: (values: ReserveCertification) => Promise<ReserveCertification>;
}

// Updates the certification parameters of a cluster for a reserve. Adding or
// removing the certification itself is handled by `UpdateReserveClustersDrawer`.
function UpdateCertificationDrawer({
  open,
  clusterName,
  clusterEnabled,
  certification,
  onClose,
  onSubmit,
}: Props) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values }: SubmitHandlerPlus<ReserveCertification>) => {
    return onSubmit(values);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDrawer
      open={open}
      title={clusterName}
      titleIcon={EditIcon}
      onCancel={onClose}
      onSubmitSuccessful={onClose}
      config={{ defaultValues: certification }}
      onSubmit={handleSubmit}
    >
      {({ control }) => (
        <Fieldset fullFieldWidth>
          <Stack direction="row" alignItems="center" gap={1.5}>
            <Typography variant="body2" color="text.secondary">
              {t("study.modeling.reserves.certifications.field.enabled")}
            </Typography>
            <Chip
              label={clusterEnabled ? t("button.yes") : t("button.no")}
              color={clusterEnabled ? "success" : "error"}
              sx={{ minWidth: 40 }}
            />
          </Stack>
          <NumberFE
            label={t("study.modeling.reserves.certifications.field.participationCost")}
            name="participationCost"
            control={control}
            rules={{
              required: t("form.field.required"),
              validate: validateNumber({ min: 0 }),
            }}
          />
          <NumberFE
            label={t("study.modeling.reserves.certifications.field.participationCostOff")}
            name="participationCostOff"
            control={control}
            rules={{
              required: t("form.field.required"),
              validate: validateNumber({ min: 0 }),
            }}
          />
          <NumberFE
            label={t("study.modeling.reserves.certifications.field.maxPower")}
            name="maxPower"
            control={control}
            rules={{
              required: t("form.field.required"),
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
              required: t("form.field.required"),
              validate: (value, { maxPower }) => validateNumber(value, { min: 0, max: maxPower }),
            }}
          />
        </Fieldset>
      )}
    </FormDrawer>
  );
}

export default UpdateCertificationDrawer;
