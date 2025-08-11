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

import SelectFE from "@/components/common/fieldEditors/SelectFE";
import type { SubmitHandlerPlus } from "@/components/common/Form/types";
import { getLink, updateLink } from "@/services/api/studies/links";
import { AssetType, TransmissionCapacity } from "@/services/api/studies/links/constants";
import type { Link, UpdateLinkParams } from "@/services/api/studies/links/types";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import type { LinkElement, StudyMetadata } from "../../../../../../../types/types";
import SwitchFE from "../../../../../../common/fieldEditors/SwitchFE";
import Fieldset from "../../../../../../common/Fieldset";
import Form from "../../../../../../common/Form";
import { getLinkUI } from "./utils";

interface Props {
  link: LinkElement;
  study: StudyMetadata;
  isOldStudy: boolean;
}

function LinkForm({ study, link, isOldStudy }: Props) {
  const { t } = useTranslation();

  const optionTransCap = Object.values(TransmissionCapacity).map((value) => ({
    label: t(`study.modelization.links.transmissionCapacities.${value}`),
    value,
  }));

  const assetTypeOptions = Object.values(AssetType).map((value) => ({
    label: t(`study.modelization.links.type.${value}`),
    value,
  }));

  const filterOptions = useMemo(
    () =>
      ["hourly", "daily", "weekly", "monthly", "annual"].map((item) => ({
        label: t(`global.time.${item}`),
        value: item,
      })),
    [t],
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ dirtyValues, values }: SubmitHandlerPlus<Link>) => {
    const { id, area1, area2, filterSynthesis, filterYearByYear, assetType, ...rest } = dirtyValues;

    let config: UpdateLinkParams["config"] = rest;

    if (filterSynthesis) {
      config.filterSynthesis = values.filterSynthesis;
    }

    if (filterYearByYear) {
      config.filterSynthesis = values.filterYearByYear;
    }

    if (assetType) {
      config = {
        ...config,
        ...getLinkUI(assetType),
      };
    }

    return updateLink({
      studyId: study.id,
      linkId: link.id,
      config,
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form
      key={link.id}
      config={{
        defaultValues: () => getLink({ studyId: study.id, linkId: link.id }),
      }}
      onSubmit={handleSubmit}
      enableUndoRedo
      hideFooterDivider
      disableStickyFooter
    >
      {({ control }) => (
        <>
          <Fieldset legend={t("global.general")}>
            <SwitchFE
              label={t("study.modelization.links.hurdleCost")}
              name="hurdlesCost"
              control={control}
            />
            <SwitchFE
              label={t("study.modelization.links.loopFlows")}
              name="loopFlow"
              control={control}
            />
            <SwitchFE
              label={t("study.modelization.links.pst")}
              name="usePhaseShifter"
              control={control}
            />
            <Fieldset.Break />
            <SelectFE
              label={t("study.modelization.links.transmissionCapacities")}
              name="transmissionCapacities"
              control={control}
              options={optionTransCap}
            />
            <SelectFE
              label={t("study.modelization.links.type")}
              name="assetType"
              control={control}
              options={assetTypeOptions}
            />
          </Fieldset>
          {!isOldStudy && (
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

export default LinkForm;
