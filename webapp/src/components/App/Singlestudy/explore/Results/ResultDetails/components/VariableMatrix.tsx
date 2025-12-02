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

import GridOffIcon from "@mui/icons-material/GridOff";
import { Skeleton } from "@mui/material";
import { useTranslation } from "react-i18next";
import type {
  DateTimes,
  EnhancedGridColumn,
  ResultMatrixDTO,
} from "@/components/common/Matrix/shared/types";
import type { UsePromiseResponse } from "@/hooks/usePromise";
import type { MatrixIndex } from "@/types/types";
import { toError } from "../../../../../../../utils/fnUtils";
import FilterableMatrixGrid, {
  type FilterableMatrixGridHandle,
} from "../../../../../../common/Matrix/components/FilterableMatrixGrid";
import { isNonEmptyMatrix } from "../../../../../../common/Matrix/shared/types";
import EmptyView from "../../../../../../common/page/EmptyView";
import UsePromiseCond from "../../../../../../common/utils/UsePromiseCond";
import type { MonteCarloMode, OutputItemType } from "../utils";
import ProcessButton from "./ProcessButton";
import type { VariablesListDTO } from "@/services/api/studies/outputs/variableViews/types";

interface VariableMatrixProps {
  variablesMetadata: VariablesListDTO | null;
  mcMode: MonteCarloMode;
  itemType: OutputItemType;
  selectedItemId: string;
  selectedVariable: string;
  isViewMaterialized: boolean;
  onMaterializeVariable: () => void;
  isMaterializing: boolean;
  matrixRes: UsePromiseResponse<ResultMatrixDTO | undefined>;
  resultColHeaders: string[][];
  filteredData: number[][];
  resultColumns: EnhancedGridColumn[];
  matrixGridRef: React.RefObject<FilterableMatrixGridHandle>;
  dateTime: DateTimes | undefined;
  dateTimeMetadata: MatrixIndex | undefined;
}

function hasVariablesForItem(
  variablesMetadata: VariablesListDTO,
  mcMode: MonteCarloMode,
  itemType: OutputItemType,
  selectedItemId: string,
): boolean {
  const data = mcMode === "mc-all" ? variablesMetadata.mcAll : variablesMetadata.mcInd;

  if (itemType === "areas") {
    return data.areas.some((a) => a.name === selectedItemId);
  }

  if (itemType === "links") {
    return data.links.some((l) => l.area1Name === selectedItemId || l.area2Name === selectedItemId);
  }

  return false;
}

function VariableMatrix({
  variablesMetadata,
  mcMode,
  itemType,
  selectedItemId,
  selectedVariable,
  isViewMaterialized,
  onMaterializeVariable,
  isMaterializing,
  matrixRes,
  resultColHeaders,
  filteredData,
  resultColumns,
  matrixGridRef,
  dateTime,
  dateTimeMetadata,
}: VariableMatrixProps) {
  const { t } = useTranslation();

  if (!variablesMetadata) {
    return <Skeleton sx={{ height: 1, transform: "none" }} />;
  }

  if (!hasVariablesForItem(variablesMetadata, mcMode, itemType, selectedItemId)) {
    return <EmptyView title={t("study.results.noVariablesForArea")} icon={GridOffIcon} />;
  }

  if (!selectedVariable) {
    return <Skeleton sx={{ height: 1, transform: "none" }} />;
  }

  if (!isViewMaterialized) {
    return (
      <EmptyView
        title={t("study.results.scanRequired")}
        icon={GridOffIcon}
        action={<ProcessButton onClick={onMaterializeVariable} loading={isMaterializing} />}
      />
    );
  }

  return (
    <UsePromiseCond
      response={matrixRes}
      ifPending={() => <Skeleton sx={{ height: 1, transform: "none" }} />}
      ifFulfilled={() => {
        if (resultColHeaders.length === 0) {
          return <Skeleton sx={{ height: 1, transform: "none" }} />;
        }

        if (!isNonEmptyMatrix(filteredData)) {
          return <EmptyView title={t("study.results.noData")} icon={GridOffIcon} />;
        }

        return (
          <FilterableMatrixGrid
            ref={matrixGridRef}
            key={`grid-${resultColHeaders.length}`}
            data={filteredData}
            rows={filteredData.length}
            columns={resultColumns}
            dateTime={dateTime}
            timeFrequency={dateTimeMetadata?.level}
            readOnly
          />
        );
      }}
      ifRejected={(err) => (
        <EmptyView
          title={
            toError(err).message.includes("404")
              ? t("study.results.noData")
              : t("data.error.matrix")
          }
          icon={GridOffIcon}
        />
      )}
    />
  );
}

export default VariableMatrix;
