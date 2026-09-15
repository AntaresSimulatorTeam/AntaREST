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
import Fieldset from "@/components/Fieldset";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import type {
  ProductionType,
  ReserveCertification,
} from "@/services/api/studies/areas/reserves/types";
import EditIcon from "@mui/icons-material/Edit";
import { Chip, Stack, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { PRODUCTION_TYPES } from "../-productionTypes";

interface Props {
  open: boolean;
  productionType: ProductionType;
  assetName: string;
  // Omitted for assets without an activation state (hydro).
  assetEnabled?: boolean;
  certification: ReserveCertification;
  onClose: VoidFunction;
  onSubmit: (values: ReserveCertification) => Promise<ReserveCertification>;
}

// Updates the certification parameters of an asset for a reserve. The fields
// depend on the production type. Adding or removing the certification itself is
// handled by `UpdateReserveAssetsDrawer`.
function UpdateCertificationDrawer({
  open,
  productionType,
  assetName,
  assetEnabled,
  certification,
  onClose,
  onSubmit,
}: Props) {
  const { t } = useTranslation();
  const { CertificationFields } = PRODUCTION_TYPES[productionType];

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
      title={assetName}
      titleIcon={EditIcon}
      onCancel={onClose}
      onSubmitSuccessful={onClose}
      config={{ defaultValues: certification }}
      onSubmit={handleSubmit}
    >
      {({ control }) => (
        <Fieldset fullFieldWidth>
          {assetEnabled !== undefined && (
            <Stack direction="row" alignItems="center" gap={1.5}>
              <Typography variant="body2" color="text.secondary">
                {t("study.modeling.reserves.certifications.field.enabled")}
              </Typography>
              <Chip
                label={assetEnabled ? t("button.yes") : t("button.no")}
                color={assetEnabled ? "success" : "error"}
                sx={{ minWidth: 40 }}
              />
            </Stack>
          )}
          <CertificationFields control={control} />
        </Fieldset>
      )}
    </FormDrawer>
  );
}

export default UpdateCertificationDrawer;
