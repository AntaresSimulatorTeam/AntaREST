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

import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { StudyMetadata } from "../../../../../../types/types";
import SelectFE from "../../../../../common/fieldEditors/SelectFE";
import SwitchFE from "../../../../../common/fieldEditors/SwitchFE";
import Fieldset from "../../../../../common/Fieldset";
import { useFormContextPlus } from "../../../../../common/Form";
import {
  LEGACY_TRANSMISSION_CAPACITIES_OPTIONS,
  SIMPLEX_OPTIMIZATION_RANGE_OPTIONS,
  toBooleanIfNeeded,
  TRANSMISSION_CAPACITIES_OPTIONS,
  UNFEASIBLE_PROBLEM_BEHAVIOR_OPTIONS,
  type OptimizationFormFields,
} from "./utils";

interface Props {
  study: StudyMetadata;
}

function Fields(props: Props) {
  const { study } = props;
  const { t } = useTranslation();
  const { control } = useFormContextPlus<OptimizationFormFields>();
  const version = Number(study.version);

  return (
    <Box>
      <Fieldset legend={t("study.configuration.optimization.legend.general")}>
        <SelectFE
          label={t("study.configuration.optimization.unfeasibleProblemBehavior")}
          options={UNFEASIBLE_PROBLEM_BEHAVIOR_OPTIONS}
          name="unfeasibleProblemBehavior"
          control={control}
        />
        <SelectFE
          label={t("study.configuration.optimization.simplexOptimizationRange")}
          options={SIMPLEX_OPTIMIZATION_RANGE_OPTIONS}
          name="simplexOptimizationRange"
          control={control}
        />
        <Fieldset.Break />
        <SwitchFE
          label={t("study.configuration.optimization.bindingConstraints")}
          name="bindingConstraints"
          control={control}
        />
        <SwitchFE
          label={t("study.configuration.optimization.hurdleCosts")}
          name="hurdleCosts"
          control={control}
        />
        <SwitchFE
          label={t("study.configuration.optimization.exportMps")}
          name="exportMps"
          control={control}
        />
      </Fieldset>
      <Fieldset legend={t("study.configuration.optimization.legend.links")}>
        <SelectFE
          label={t("study.configuration.optimization.transmissionCapacities")}
          options={
            version >= 840
              ? TRANSMISSION_CAPACITIES_OPTIONS
              : LEGACY_TRANSMISSION_CAPACITIES_OPTIONS
          }
          name="transmissionCapacities"
          control={control}
          rules={{ setValueAs: toBooleanIfNeeded }}
        />
      </Fieldset>
      <Fieldset legend={t("study.configuration.optimization.legend.thermalClusters")}>
        <SwitchFE
          label={t("study.configuration.optimization.thermalClustersMinStablePower")}
          name="thermalClustersMinStablePower"
          control={control}
        />
        <SwitchFE
          label={t("study.configuration.optimization.thermalClustersMinUdTime")}
          name="thermalClustersMinUdTime"
          control={control}
        />
      </Fieldset>
      <Fieldset legend={t("study.configuration.optimization.legend.reserve")}>
        <SwitchFE
          label={t("study.configuration.optimization.dayAheadReserve")}
          name="dayAheadReserve"
          control={control}
        />
        <SwitchFE
          label={t("study.configuration.optimization.primaryReserve")}
          name="primaryReserve"
          control={control}
        />
        <SwitchFE
          label={t("study.configuration.optimization.strategicReserve")}
          name="strategicReserve"
          control={control}
        />
        <SwitchFE
          label={t("study.configuration.optimization.spinningReserve")}
          name="spinningReserve"
          control={control}
        />
      </Fieldset>
    </Box>
  );
}

export default Fields;
