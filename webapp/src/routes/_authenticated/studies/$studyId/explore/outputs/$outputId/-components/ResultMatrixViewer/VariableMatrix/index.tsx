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

import FilterableMatrixGrid, {
  type FilterableMatrixGridHandle,
} from "@/components/Matrix/components/FilterableMatrixGrid";
import {
  isNonEmptyMatrix,
  type DateTimeMetadataDTO,
  type DateTimes,
  type EnhancedGridColumn,
} from "@/components/Matrix/shared/types";
import EmptyView from "@/components/page/EmptyView";
import UsePromiseCond from "@/components/utils/UsePromiseCond";
import type { UsePromiseResponse } from "@/hooks/usePromise";
import type {
  VariablesListDTO,
  VariableViewMatrixDTO,
} from "@/services/api/studies/outputs/variableViews/types";
import type { Area, LinkElement } from "@/types/types";
import GridOffIcon from "@mui/icons-material/GridOff";
import { Skeleton } from "@mui/material";
import { isAxiosError } from "axios";
import { useTranslation } from "react-i18next";
import type { OutputItemType } from "../../../-utils";
import ProcessButton from "./ProcessButton";

interface VariableMatrixProps {
  variablesMetadata: VariablesListDTO | null;
  itemType: OutputItemType;
  selectedItemId: string;
  selectedItem: (Area & { id: string }) | LinkElement | undefined;
  onMaterializeVariable: () => void;
  isMaterializing: boolean;
  variableViewDataRes: UsePromiseResponse<VariableViewMatrixDTO | null>;
  resultColumns: EnhancedGridColumn[];
  matrixGridRef: React.RefObject<FilterableMatrixGridHandle>;
  dateTime?: DateTimes;
  dateTimeMetadata?: DateTimeMetadataDTO;
}

function hasVariablesForItem(
  variablesMetadata: VariablesListDTO,
  itemType: OutputItemType,
  selectedItemId: string,
  selectedItem: (Area & { id: string }) | LinkElement | undefined,
): boolean {
  // Variable-per-variable always uses mcInd
  const data = variablesMetadata.mcInd;

  if (itemType === "areas") {
    return data.areas.some((area) => area.name === selectedItemId);
  }

  if (itemType === "links" && selectedItem && "area1" in selectedItem) {
    return data.links.some(
      (link) => link.area1Name === selectedItem.area1 && link.area2Name === selectedItem.area2,
    );
  }

  return false;
}

function VariableMatrix({
  variablesMetadata,
  itemType,
  selectedItemId,
  selectedItem,
  onMaterializeVariable,
  isMaterializing,
  variableViewDataRes,
  resultColumns,
  matrixGridRef,
  dateTime,
  dateTimeMetadata,
}: VariableMatrixProps) {
  const { t } = useTranslation();

  // TODO: !variablesMetadata check may be unnecessary
  if (
    !variablesMetadata ||
    !hasVariablesForItem(variablesMetadata, itemType, selectedItemId, selectedItem)
  ) {
    return <EmptyView title={t("study.outputs.noVariablesForArea")} icon={GridOffIcon} />;
  }

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={variableViewDataRes}
      ifPending={() => <Skeleton sx={{ height: 1, transform: "none" }} />}
      ifFulfilled={(matrix) => {
        if (!matrix || !isNonEmptyMatrix(matrix.data)) {
          return <EmptyView title={t("study.outputs.noData")} icon={GridOffIcon} />;
        }

        return (
          <FilterableMatrixGrid
            ref={matrixGridRef}
            key={`grid-${matrix.columns.length}`}
            data={matrix.data}
            rows={matrix.data.length}
            columns={resultColumns}
            dateTime={dateTime}
            timeFrequency={dateTimeMetadata?.level}
            readOnly
          />
        );
      }}
      ifRejected={(err) => {
        const error = isAxiosError(err) ? err.response?.data : undefined;
        const status = error?.status;
        const taskId = error?.task_id;

        // NOT_FOUND status with no task ID means data not materialized yet
        if (status === "NOT_FOUND" && taskId === null) {
          // TODO: update the status to "NOT_MATERIALIZED" + handle the ongoing materialization
          // state using the taskId and the "IN_PROGRESS" status
          return (
            <EmptyView
              title={t("study.outputs.scanRequired")}
              icon={GridOffIcon}
              actions={<ProcessButton onClick={onMaterializeVariable} loading={isMaterializing} />}
            />
          );
        }

        // Other 404 errors (variable doesn't exist, invalid data, etc.)
        return <EmptyView title={t("data.error.matrix")} icon={GridOffIcon} />;
      }}
    />
  );
}

export default VariableMatrix;
