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

import SelectFE, { type Options } from "@/components/fieldEditors/SelectFE";
import SwitchFE from "@/components/fieldEditors/SwitchFE";
import Fieldset from "@/components/Fieldset";
import Form from "@/components/Form";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import useStudy from "@/routes/-shared/hook/useStudy";
import { getLink, updateLink } from "@/services/api/studies/links";
import { AssetType, TransmissionCapacity } from "@/services/api/studies/links/constants";
import type {
  AssetTypeValue,
  Link,
  TransmissionCapacityValue,
} from "@/services/api/studies/links/types";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import semver from "semver";
import { getLinkUI } from "./utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/links/$linkId/properties",
)({
  component: Parameters,
});

const optionTransCap: Options<TransmissionCapacityValue> = Object.values(TransmissionCapacity).map(
  (value) => ({
    label: (t) => t(`study.modeling.links.transmissionCapacities.${value}`),
    value,
  }),
);

const assetTypeOptions: Options<AssetTypeValue> = Object.values(AssetType).map((value) => ({
  label: (t) => t(`study.modeling.links.type.${value}`),
  value,
}));

const FILTERS = ["hourly", "daily", "weekly", "monthly", "annual"] as const;

const filterOptions: Options<(typeof FILTERS)[number]> = FILTERS.map((item) => ({
  label: (t) => t(`global.time.${item}`),
  value: item,
}));

function Parameters() {
  const { studyId, linkId } = Route.useParams();
  const study = useStudy();
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ dirtyValues }: SubmitHandlerPlus<Link>) => {
    const { id, area1, area2, assetType, ...config } = dirtyValues;

    return updateLink({
      studyId,
      linkId,
      config: assetType
        ? {
            ...config,
            ...getLinkUI(assetType),
          }
        : config,
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form
      key={linkId}
      config={{ defaultValues: () => getLink({ studyId, linkId }) }}
      onSubmit={handleSubmit}
      enableUndoRedo
    >
      {({ control }) => (
        <>
          <Fieldset legend={t("global.general")}>
            <SwitchFE
              label={t("study.modeling.links.hurdleCost")}
              name="hurdlesCost"
              control={control}
            />
            <SwitchFE
              label={t("study.modeling.links.loopFlows")}
              name="loopFlow"
              control={control}
            />
            <SwitchFE
              label={t("study.modeling.links.pst")}
              name="usePhaseShifter"
              control={control}
            />
            <Fieldset.Break />
            <SelectFE
              label={t("study.modeling.links.transmissionCapacities")}
              name="transmissionCapacities"
              control={control}
              options={optionTransCap}
            />
            <SelectFE
              label={t("study.modeling.links.type")}
              name="assetType"
              control={control}
              options={assetTypeOptions}
            />
          </Fieldset>
          {semver.gte(study.version, "8.2.0") && (
            <Fieldset legend={t("study.outputFilters")}>
              <SelectFE
                label={t(`study.outputFilters.filterSynthesis`)}
                name="filterSynthesis"
                control={control}
                multiple
                options={filterOptions}
                variant="outlined"
                sx={{ maxWidth: 220 }}
              />
              <SelectFE
                label={t(`study.outputFilters.filterByYear`)}
                name="filterYearByYear"
                control={control}
                options={filterOptions}
                multiple
                variant="outlined"
                sx={{ maxWidth: 220 }}
              />
            </Fieldset>
          )}
        </>
      )}
    </Form>
  );
}
