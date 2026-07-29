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

import type { MatrixFilterHandle } from "@/components/Matrix/components/MatrixFilter/types";
import ViewWrapper from "@/components/page/ViewWrapper";
import { useMemo, useRef, useState } from "react";
import { type DataType, type Frequency, type Item, type MonteCarloMode } from "../../-utils";
import Header from "./Header";
import OutputContext, { type OutputContextValue } from "./OutputContext";
import OutputMatrix from "./OutputMatrix";
import OutputVariableMatrix from "./OutputVariableMatrix";
import { DEFAULT_COLUMNS_FILTERS, type ColumnsFiltersData } from "./utils";

interface Props {
  item: Item;
}

function OutputMatrixViewer({ item }: Props) {
  const [monteCarloMode, setMonteCarloMode] = useState<MonteCarloMode>("mc-all");
  const [dataType, setDataType] = useState<DataType>("values");
  const [frequency, setFrequency] = useState<Frequency>("hourly");
  const [year, setYear] = useState(-1);
  const [variable, setVariable] = useState("");
  const [clusterId, setClusterId] = useState<string>("");
  const [columnsFilters, setColumnsFilters] = useState<ColumnsFiltersData>(DEFAULT_COLUMNS_FILTERS);
  const [isMatrixDataLoaded, setIsMatrixDataLoaded] = useState(false);
  const matrixGridRef = useRef<MatrixFilterHandle>(null);

  const contextValue = useMemo(
    () =>
      ({
        item,
        isMatrixDataLoaded,
        setIsMatrixDataLoaded,
        monteCarloMode,
        setMonteCarloMode,
        year,
        setYear,
        dataType,
        setDataType,
        frequency,
        setFrequency,
        variable,
        setVariable,
        clusterId,
        setClusterId,
        columnsFilters,
        setColumnsFilters,
        matrixGridRef,
      }) satisfies OutputContextValue,
    [
      item,
      isMatrixDataLoaded,
      setIsMatrixDataLoaded,
      monteCarloMode,
      setMonteCarloMode,
      year,
      setYear,
      dataType,
      setDataType,
      frequency,
      setFrequency,
      variable,
      setVariable,
      clusterId,
      setClusterId,
      columnsFilters,
      setColumnsFilters,
    ],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ViewWrapper flex={{ gap: 1.5 }}>
      <OutputContext value={contextValue}>
        <Header />
        {monteCarloMode === "variable-per-variable" ? <OutputVariableMatrix /> : <OutputMatrix />}
      </OutputContext>
    </ViewWrapper>
  );
}

export default OutputMatrixViewer;
