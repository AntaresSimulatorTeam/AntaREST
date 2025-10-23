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

import { GridCellKind, type GridColumn, type Item } from "@glideapps/glide-data-grid";
import * as R from "ramda";
import { useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router";
import { updateScenarioBuilderForm } from "@/services/api/studies/config/scenarioBuilder";
import type {
  ScenarioDisplay,
  ScenarioType,
} from "@/services/api/studies/config/scenarioBuilder/types";
import useEnqueueErrorSnackbar from "../../../../../../../../hooks/useEnqueueErrorSnackbar";
import type { StudyMetadata } from "../../../../../../../../types/types";
import { toError } from "../../../../../../../../utils/fnUtils";
import DataGridForm from "../../../../../../../common/DataGridForm";
import type { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import EmptyView from "../../../../../../../common/page/EmptyView";

interface Props {
  config: ScenarioDisplay;
  type: ScenarioType;
  areaId?: string;
}

function Table({ config, type, areaId }: Props) {
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { study } = useOutletContext<{ study: StudyMetadata }>();

  const rowNames = useMemo(() => R.keys(config), [config]);

  const columns = useMemo<Array<GridColumn & { id: string }>>(() => {
    if (rowNames.length === 0) {
      return [];
    }

    // Get the year indices from the first row
    const firstRowData = config[rowNames[0]] as Record<string, number | "">;
    const yearIndices = Object.keys(firstRowData);

    return yearIndices.map((yearIndex) => ({
      id: yearIndex,
      title: `${t("global.year")} ${Number(yearIndex) + 1}`,
    }));
  }, [config, rowNames, t]);

  const defaultData = useMemo(() => {
    return rowNames.reduce(
      (acc, rowName) => {
        acc[rowName] = config[rowName] as Record<string, number | "">;
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
      key={JSON.stringify(defaultData)}
      defaultData={defaultData}
      columns={columns}
      getCellContent={getCellContent}
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
