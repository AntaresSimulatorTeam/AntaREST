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

import DataGridForm, { type GridSubmitHandlerPlus } from "@/components/DataGridForm";
import ViewWrapper from "@/components/page/ViewWrapper";
import {
  createScenario,
  deleteScenario,
  getScenarioBuilder,
  updateScenario,
} from "@/services/api/studies/gems/scenarioBuilder";
import type { ScenarioBuilder } from "@/services/api/studies/gems/scenarioBuilder/types";
import { buildKey } from "@/utils/reactUtils";
import { GridCellKind, type Item, type NumberCell } from "@glideapps/glide-data-grid";
import { createFileRoute } from "@tanstack/react-router";
import { useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import useStudy from "../../../../-hooks/useStudy";
import {
  adaptScenarioBuilderToGridForm,
  adaptScenarioFormToScenarioDto,
  type ScenarioBuilderGridForm,
} from "./-utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/configuration/gems/scenario-builder/",
)({
  loader: async ({ params: { studyId } }) => {
    const scenarioBuilder = await getScenarioBuilder({ studyId });
    return adaptScenarioBuilderToGridForm(scenarioBuilder);
  },
  staleTime: 0, // Force refetch on each visit
  component: ScenarioBuilder,
});

function ScenarioBuilder() {
  const { t } = useTranslation();
  const defaultData = Route.useLoaderData();
  const isLoading = Route.useMatch({ select: (match) => match.isFetching !== false });
  const study = useStudy();

  // createScenario({
  //   studyId: study.id,
  //   scenarioName: "test1",
  //   value: [{ scenario: 9, timeSeriesIndex: 8 }],
  // });

  const columns = useMemo(() => {
    const maxYearIndex = Math.max(
      0, // Ensures at least one year column, even without data
      ...Object.values(defaultData).flatMap((scenario) => Object.keys(scenario).map(Number)),
    );

    return Array.from({ length: maxYearIndex + 1 }, (_, yearIndex) => ({
      id: yearIndex.toString(),
      title: `${t("global.year")} ${yearIndex + 1}`,
    }));
  }, [defaultData, t]);

  ////////////////////////////////////////////////////////////////
  // Cells
  ////////////////////////////////////////////////////////////////

  const getCellContent = useCallback((_: Item, cellData: number | "") => {
    if (typeof cellData === "number") {
      return {
        kind: GridCellKind.Number,
        data: cellData,
        displayData: cellData.toString(),
        allowOverlay: true,
      } satisfies NumberCell;
    }

    // Empty string should display "rand" but allow numeric input
    return {
      kind: GridCellKind.Number,
      data: undefined,
      displayData: "rand",
      allowOverlay: true,
    } satisfies NumberCell;
  }, []);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////
  const handleSubmit = async ({
    changes,
    markAsSaved,
  }: GridSubmitHandlerPlus<ScenarioBuilderGridForm>) => {
    const { added, updated, deleted } = changes;
    const studyId = study.id;

    // Each row is marked as saved as soon as its request succeeds, so if another
    // request fails, it won't be included again in the next submit's changes.

    const addPromises = Object.entries(added).flatMap(([scenarioName, newScenario]) =>
      newScenario
        ? createScenario({
            studyId,
            scenarioName,
            value: adaptScenarioFormToScenarioDto(newScenario),
          }).then(() => markAsSaved(scenarioName))
        : [],
    );

    const updatePromises = Object.entries(updated).flatMap(([scenarioName, dirtyScenario]) =>
      dirtyScenario
        ? updateScenario({
            studyId,
            scenarioName,
            value: adaptScenarioFormToScenarioDto(dirtyScenario),
          }).then(() => markAsSaved(scenarioName))
        : [],
    );

    const deletePromises = deleted.map((scenarioName) =>
      deleteScenario({ studyId, scenarioName: String(scenarioName) }).then(() =>
        markAsSaved(scenarioName),
      ),
    );

    // Wait for all requests (even if some fail), then rethrow the first error
    // so the form displays it
    const results = await Promise.allSettled([
      ...addPromises,
      ...updatePromises,
      ...deletePromises,
    ]);

    const failure = results.find(
      (result): result is PromiseRejectedResult => result.status === "rejected",
    );

    if (failure) {
      throw failure.reason;
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ViewWrapper>
      <DataGridForm
        key={buildKey(isLoading)}
        defaultData={defaultData}
        columns={columns}
        getCellContent={getCellContent}
        onSubmit={handleSubmit}
        isLoading={isLoading}
        allowRowDeletion
      />
    </ViewWrapper>
  );
}
