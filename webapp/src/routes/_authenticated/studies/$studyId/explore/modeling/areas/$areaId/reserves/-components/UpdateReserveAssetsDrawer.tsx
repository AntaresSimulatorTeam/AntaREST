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

import CheckboxesTagsFE from "@/components/fieldEditors/CheckboxesTagsFE";
import Fieldset from "@/components/Fieldset";
import FormDrawer from "@/components/FormDrawer";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import FactoryIcon from "@mui/icons-material/Factory";
import { Alert, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { ReserveAsset } from "../-productionTypes";
import { sortByName } from "@/services/utils";

interface FormValues {
  assetIds: string[];
}

interface Props {
  open: boolean;
  reserveName: string;
  /** Label of the asset field, i.e. the production type's name. */
  label: string;
  assets: ReserveAsset[];
  /** IDs of the assets currently certified for the reserve. */
  defaultValues: string[];
  onClose: VoidFunction;
  onSubmit: (assetIds: string[]) => Promise<string[]>;
}

// Multi-select of the assets of one production type certified for a reserve.
// Deselecting an asset removes its certification and deletes its parameters.
function UpdateReserveAssetsDrawer({
  open,
  reserveName,
  label,
  assets,
  defaultValues,
  onClose,
  onSubmit,
}: Props) {
  const { t } = useTranslation();

  const assetNamesById = new Map(assets.map(({ id, name }) => [id, name]));

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async ({ values }: SubmitHandlerPlus<FormValues>): Promise<FormValues> => {
    return { assetIds: await onSubmit(values.assetIds) };
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDrawer
      open={open}
      title={reserveName}
      titleIcon={FactoryIcon}
      onCancel={onClose}
      onSubmitSuccessful={onClose}
      config={{ defaultValues: { assetIds: defaultValues } }}
      onSubmit={handleSubmit}
    >
      {({ control, watch }) => {
        const selectedIds = watch("assetIds");

        // Certified assets that are deselected lose their parameters on save
        const removedNames = defaultValues
          .filter((id) => !selectedIds.includes(id))
          .map((id) => assetNamesById.get(id) ?? id);

        return (
          <Fieldset fullFieldWidth>
            {assets.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                {t("study.modeling.reserves.certifications.noClusters")}
              </Typography>
            ) : (
              <CheckboxesTagsFE
                label={label}
                options={sortByName(assets).map((asset) => asset.id)}
                getOptionLabel={(id) => assetNamesById.get(id) ?? id}
                name="assetIds"
                control={control}
              />
            )}
            {removedNames.length > 0 && (
              <Alert severity="warning">
                {t("study.modeling.reserves.certifications.removeWarning", {
                  clusters: removedNames,
                })}
              </Alert>
            )}
          </Fieldset>
        );
      }}
    </FormDrawer>
  );
}

export default UpdateReserveAssetsDrawer;
