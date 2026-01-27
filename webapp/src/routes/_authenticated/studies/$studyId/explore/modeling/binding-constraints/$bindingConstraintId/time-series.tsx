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

import DataGridSkeleton from "@/components/DataGridSkeleton";
import Matrix from "@/components/Matrix";
import SplitView from "@/components/page/SplitView";
import UsePromiseCond from "@/components/utils/UsePromiseCond";
import usePromise from "@/hooks/usePromise";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import { getBindingConstraint } from "@/services/api/studies/bindingConstraints";
import { Box } from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import semver from "semver";
import useBindingConstraint from "./-hooks/useBindingConstraint";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/binding-constraints/$bindingConstraintId/time-series",
)({
  component: TimeSeries,
});

function TimeSeries() {
  const study = useStudy();
  const constraint = useBindingConstraint();
  const { t } = useTranslation();
  const baseUrl = `input/bindingconstraints/${constraint.id}`;

  /**
   * Determines whether the binding constraint uses deterministic or scenarized time-series:
   *
   * - Deterministic (< v8.7.0): Single matrix with fixed bound values for all Monte Carlo years.
   *   The matrix contains columns for "<", ">", and "=" operators in one combined view.
   *
   * - Scenarized (>= v8.7.0): Supports multiple time-series for Monte Carlo scenario building.
   *   Separate matrices (`_lt`, `_eq`, `_gt`) allow different bound values per scenario,
   *   enabling stochastic modeling of constraint bounds.
   */
  const isDeterministic = semver.lt(study.version, "8.7.0");

  const response = usePromise(
    () => {
      return getBindingConstraint({
        studyId: study.id,
        constraintId: constraint.id,
      });
    },
    {
      deps: [study.id, constraint.id],
      disabled: isDeterministic,
    },
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (constraint.isOptimistic) {
    return <DataGridSkeleton />;
  }

  if (isDeterministic) {
    return (
      <Matrix
        key={constraint.id}
        studyId={study.id}
        title={t("global.matrix")}
        url={baseUrl}
        customColumns={["<", ">", "="]}
      />
    );
  }

  return (
    <UsePromiseCond
      response={response}
      ifPending={() => <DataGridSkeleton />}
      ifFulfilled={({ operator }) => (
        <>
          {operator === "less" && (
            <Matrix
              key={constraint.id}
              studyId={study.id}
              title={t("study.modeling.bindingConst.timeSeries.less")}
              url={`${baseUrl}_lt`}
            />
          )}
          {operator === "equal" && (
            <Matrix
              key={constraint.id}
              studyId={study.id}
              title={t("study.modeling.bindingConst.timeSeries.equal")}
              url={`${baseUrl}_eq`}
            />
          )}
          {operator === "greater" && (
            <Matrix
              key={constraint.id}
              studyId={study.id}
              title={t("study.modeling.bindingConst.timeSeries.greater")}
              url={`${baseUrl}_gt`}
            />
          )}
          {operator === "both" && (
            <SplitView splitId="binding-constraints-matrix" sizes={[50, 50]}>
              <Box sx={{ p: 2 }}>
                <Matrix
                  key={constraint.id}
                  studyId={study.id}
                  title={t("study.modeling.bindingConst.timeSeries.less")}
                  url={`${baseUrl}_lt`}
                />
              </Box>
              <Box sx={{ p: 2 }}>
                <Matrix
                  key={constraint.id}
                  studyId={study.id}
                  title={t("study.modeling.bindingConst.timeSeries.greater")}
                  url={`${baseUrl}_gt`}
                />
              </Box>
            </SplitView>
          )}
        </>
      )}
    />
  );
}
