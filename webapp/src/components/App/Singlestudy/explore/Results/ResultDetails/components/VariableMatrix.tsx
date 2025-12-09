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

/**
 * Variable Matrix Component for Variable-per-Variable Views
 *
 * This component displays the consolidated matrix view for a specific variable across all years
 * in the variable-per-variable mode.
 *
 * DATA SOURCE RATIONALE:
 * This component exclusively uses mcInd (Monte Carlo Individual) data from the variables metadata.
 * Although the API endpoint /v1/studies/{uuid}/output/{output_id}/variables-list returns both
 * mcInd and mcAll in a single response, we only use mcInd here because:
 *
 * - mcInd: Contains non-aggregated, year-by-year individual simulation data
 *   → Perfect for variable-per-variable views where users want to see detailed data across all years
 *   → Eliminates the need to navigate through potentially 1000+ individual matrices
 *
 * - mcAll: Contains pre-aggregated statistics (sum, standard deviation, etc.) across all simulations
 *   → Already synthesized, so a single matrix view is sufficient (used in Synthesis view)
 *   → Does not benefit from variable-by-variable breakdown
 *
 * The API keeps both in a single endpoint for practical reasons (splitting was deemed impractical),
 * but the front-end primarily consumes mcInd for variable-per-variable features.
 *
 * Note: Variable lists may differ between mcInd and mcAll for the same area/link.
 */

import GridOffIcon from "@mui/icons-material/GridOff";
import { Skeleton } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { EnhancedGridColumn } from "@/components/common/Matrix/shared/types";
import type { UsePromiseResponse } from "@/hooks/usePromise";
import type {
  VariablesListDTO,
  VariableViewMatrixDTO,
} from "@/services/api/studies/outputs/variableViews/types";
import type { Area, LinkElement } from "@/types/types";
import { toError } from "../../../../../../../utils/fnUtils";
import FilterableMatrixGrid, {
  type FilterableMatrixGridHandle,
} from "../../../../../../common/Matrix/components/FilterableMatrixGrid";
import { isNonEmptyMatrix } from "../../../../../../common/Matrix/shared/types";
import EmptyView from "../../../../../../common/page/EmptyView";
import UsePromiseCond from "../../../../../../common/utils/UsePromiseCond";
import type { OutputItemType } from "../utils";
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
}: VariableMatrixProps) {
  const { t } = useTranslation();

  // TODO: !variablesMetadata check may be unnecessary
  if (
    !variablesMetadata ||
    !hasVariablesForItem(variablesMetadata, itemType, selectedItemId, selectedItem)
  ) {
    return <EmptyView title={t("study.results.noVariablesForArea")} icon={GridOffIcon} />;
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
          return <EmptyView title={t("study.results.noData")} icon={GridOffIcon} />;
        }

        return (
          <FilterableMatrixGrid
            ref={matrixGridRef}
            key={`grid-${matrix.columns.length}`}
            data={matrix.data}
            rows={matrix.data.length}
            columns={resultColumns}
            readOnly
          />
        );
      }}
      ifRejected={(err) => {
        const errorMessage = toError(err).message;
        const isNotFound = errorMessage.includes("404") || errorMessage.includes("not found");

        // The output variables view is not materialized in DB yet
        if (isNotFound) {
          return (
            <EmptyView
              title={t("study.results.scanRequired")}
              icon={GridOffIcon}
              action={<ProcessButton onClick={onMaterializeVariable} loading={isMaterializing} />}
            />
          );
        }

        return <EmptyView title={t("data.error.matrix")} icon={GridOffIcon} />;
      }}
    />
  );
}

export default VariableMatrix;
