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

import DataGridForm from "@/components/DataGridForm";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import EmptyView from "@/components/page/EmptyView";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import { updateScenarioBuilderForm } from "@/services/api/studies/config/scenarioBuilder";
import type {
  Level1Display,
  ScenarioType,
} from "@/services/api/studies/config/scenarioBuilder/types";
import { GridCellKind, type GridColumn, type Item } from "@glideapps/glide-data-grid";
import * as R from "ramda";
import { useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import useEnqueueErrorSnackbar from "../../../../../../../../../../hooks/useEnqueueErrorSnackbar";
import { toError } from "../../../../../../../../../../utils/fnUtils";

interface Props {
  config: Level1Display;
  type: ScenarioType;
  areaId?: string;
}

function Table({ config, type, areaId }: Props) {
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const study = useStudy();

  const rowNames = useMemo(() => R.keys(config), [config]);

  const columns = useMemo<Array<GridColumn & { id: string }>>(() => {
    if (rowNames.length === 0) {
      return [];
    }

    // Get the MC year indices from the first row
    const firstRowName = rowNames[0];
    const firstRowData = config[firstRowName];
    const yearIndices = R.keys(firstRowData);

    return yearIndices.map((yearIndex) => ({
      id: yearIndex,
      title: `${t("global.year")} ${Number(yearIndex) + 1}`,
    }));
  }, [config, rowNames, t]);

  const defaultData = useMemo(() => {
    return rowNames.reduce(
      (acc, rowName) => {
        acc[rowName] = config[rowName];
        return acc;
      },
      {} as Record<string, Record<string, number | "">>,
    );
  }, [config, rowNames]);

  const getCellContent = useCallback((_location: Item, cellData: number | "") => {
    if (typeof cellData === "number") {
      return {
        kind: GridCellKind.Number,
        data: cellData,
        displayData: cellData.toString(),
        allowOverlay: true,
      } as const;
    }

    // Empty string should display "rand" but allow numeric input
    return {
      kind: GridCellKind.Number,
      data: undefined,
      displayData: "rand",
      allowOverlay: true,
    } as const;
  }, []);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const transformCellValue = useCallback((_location: Item, newValue: unknown) => {
    // Handle clearing a cell when user deletes content, return empty string to display "rand"
    if (newValue === undefined) {
      return ""; // Reset to "rand"
    }

    // Return undefined to let DataGridForm handle it normally
    return undefined;
  }, []);

  const handleSubmit = async ({ dirtyValues }: SubmitHandlerPlus) => {
    try {
      await updateScenarioBuilderForm({
        studyId: study.id,
        scenarioType: type,
        values: dirtyValues,
        areaId,
      });
    } catch (error) {
      enqueueErrorSnackbar(
        t("study.configuration.general.mcScenarioBuilder.update.error", {
          type,
        }),
        toError(error),
      );
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (Object.keys(config).length === 0) {
    return <EmptyView title="No scenario configuration." />;
  }

  return (
    <DataGridForm
      key={JSON.stringify(config)}
      defaultData={defaultData}
      columns={columns}
      getCellContent={getCellContent}
      transformCellValue={transformCellValue}
      onSubmit={handleSubmit}
      rowMarkers={{
        kind: "clickable-string",
        getTitle: (index) => rowNames[index],
        width: 150,
      }}
    />
  );
}

export default Table;
