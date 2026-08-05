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
import { reserveQueries } from "@/queries/reserves/queries";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import useArea from "@/routes/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/-hooks/useArea";
import type {
  CertificationProductionType,
  Reserve,
} from "@/services/api/studies/areas/reserves/types";
import FactoryIcon from "@mui/icons-material/Factory";
import { Alert, Typography } from "@mui/material";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { thermalClustersQueries } from "../-utils";

// One entry per production type ("thermals" for now, "storages" and "hydro" coming soon)
export type ClustersFormValues = Record<CertificationProductionType, string[]>;

interface Props {
  open: boolean;
  reserveId: Reserve["id"];
  defaultValues: ClustersFormValues;
  onClose: VoidFunction;
  onSubmit: (values: ClustersFormValues) => Promise<ClustersFormValues>;
}

// Multi-select of the clusters certified for a reserve, one field per production
// type. Deselecting a cluster removes its certification and deletes its parameters.
function UpdateReserveClustersDrawer({ open, reserveId, defaultValues, onClose, onSubmit }: Props) {
  const { t } = useTranslation();
  const { id: studyId } = useStudy();
  const { id: areaId } = useArea();

  const { data: reserves } = useSuspenseQuery(reserveQueries.list(studyId, areaId));
  const { data: thermalClusters } = useSuspenseQuery(thermalClustersQueries.list(studyId, areaId));

  const reserveName = reserves.find(({ id }) => id === reserveId)?.name ?? reserveId;

  // One entry per production type ("storages" and "hydro" sections will be
  // added once their endpoints are released)
  const sections = [
    {
      productionType: "thermals" as const,
      label: t("study.modeling.reserves.certifications.productionType.thermals"),
      clusters: thermalClusters,
    },
  ];

  const clusterNamesById = new Map(
    sections.flatMap((section) => section.clusters.map(({ id, name }) => [id, name] as const)),
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values }: SubmitHandlerPlus<ClustersFormValues>) => {
    return onSubmit(values);
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
      config={{ defaultValues }}
      onSubmit={handleSubmit}
    >
      {({ control, watch }) => {
        // Certified clusters that are deselected lose their parameters on save
        const removedNames = sections.flatMap((section) => {
          const selectedIds = watch(section.productionType) ?? [];
          return defaultValues[section.productionType]
            .filter((id) => !selectedIds.includes(id))
            .map((id) => clusterNamesById.get(id) ?? id);
        });

        return (
          <Fieldset fullFieldWidth>
            {sections.map((section) =>
              section.clusters.length === 0 ? (
                <Typography key={section.productionType} variant="body2" color="text.secondary">
                  {t("study.modeling.reserves.certifications.noClusters")}
                </Typography>
              ) : (
                <CheckboxesTagsFE
                  key={section.productionType}
                  label={section.label}
                  options={section.clusters.map((cluster) => cluster.id)}
                  getOptionLabel={(id) => clusterNamesById.get(id) ?? id}
                  name={section.productionType}
                  control={control}
                />
              ),
            )}
            {removedNames.length > 0 && (
              <Alert severity="warning">
                {t("study.modeling.reserves.certifications.removeWarning", {
                  clusters: removedNames.join(", "),
                })}
              </Alert>
            )}
          </Fieldset>
        );
      }}
    </FormDrawer>
  );
}

export default UpdateReserveClustersDrawer;
