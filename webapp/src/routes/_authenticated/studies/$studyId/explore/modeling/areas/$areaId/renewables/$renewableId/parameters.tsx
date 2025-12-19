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

import NumberFE from "@/components/fieldEditors/NumberFE";
import SelectFE from "@/components/fieldEditors/SelectFE";
import StringFE from "@/components/fieldEditors/StringFE";
import SwitchFE from "@/components/fieldEditors/SwitchFE";
import Fieldset from "@/components/Fieldset";
import Form from "@/components/Form";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import useArea from "@/routes/-shared/hook/useArea";
import useStudy from "@/routes/-shared/hook/useStudy";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import semver from "semver";
import {
  getRenewableCluster,
  RENEWABLE_GROUPS,
  TS_INTERPRETATION_OPTIONS,
  updateRenewableCluster,
  type RenewableCluster,
} from "../-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/renewables/$renewableId/parameters",
)({
  component: Parameters,
});

function Parameters() {
  const study = useStudy();
  const area = useArea();
  const { renewableId } = Route.useParams();
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ dirtyValues }: SubmitHandlerPlus<RenewableCluster>) => {
    return updateRenewableCluster(study.id, area.id, renewableId, dirtyValues);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form
      key={renewableId}
      config={{ defaultValues: () => getRenewableCluster(study.id, area.id, renewableId) }}
      onSubmit={handleSubmit}
      enableUndoRedo
      disableStickyFooter
      hideFooterDivider
    >
      {({ control }) => (
        <Fieldset legend={t("study.modeling.clusters.operatingParameters")}>
          <StringFE label={t("global.name")} name="name" control={control} disabled />
          {semver.lt(study.version, "9.3.0") ? (
            <SelectFE
              label={t("global.group")}
              name="group"
              control={control}
              options={RENEWABLE_GROUPS}
              startCaseLabel={false}
              sx={{
                alignSelf: "center",
              }}
            />
          ) : (
            <StringFE
              label={t("global.group")}
              name="group"
              datalist={RENEWABLE_GROUPS}
              control={control}
            />
          )}
          <SwitchFE label={t("study.modeling.clusters.enabled")} name="enabled" control={control} />
          <SelectFE
            label={t("study.modeling.clusters.tsInterpretation")}
            name="tsInterpretation"
            control={control}
            options={TS_INTERPRETATION_OPTIONS}
            sx={{
              alignSelf: "center",
            }}
          />
          <NumberFE
            label={t("study.modeling.clusters.unitcount")}
            name="unitCount"
            control={control}
            rules={{
              min: {
                value: 1,
                message: t("form.field.minValue", { 0: 1 }),
              },
              setValueAs: Math.floor,
            }}
          />
          <NumberFE
            label={t("study.modeling.clusters.nominalCapacity")}
            name="nominalCapacity"
            control={control}
            rules={{
              min: {
                value: 0,
                message: t("form.field.minValue", { 0: 0 }),
              },
            }}
          />
        </Fieldset>
      )}
    </Form>
  );
}
