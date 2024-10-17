/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { useEffect, useState } from "react";
import { StudyMetadata } from "../../common/types";
import usePromise from "../../hooks/usePromise";
import {
  getTableMode,
  setTableMode,
} from "../../services/api/studies/tableMode";
import {
  TableData,
  TableModeColumnsForType,
  TableModeType,
} from "../../services/api/studies/tableMode/types";
import { SubmitHandlerPlus } from "./Form/types";
import TableForm from "./TableForm";
import UsePromiseCond from "./utils/UsePromiseCond";
import GridOffIcon from "@mui/icons-material/GridOff";
import EmptyView from "./page/SimpleContent";
import { useTranslation } from "react-i18next";

export interface TableModeProps<T extends TableModeType = TableModeType> {
  studyId: StudyMetadata["id"];
  type: T;
  columns: TableModeColumnsForType<T>;
}

function TableMode<T extends TableModeType>(props: TableModeProps<T>) {
  const { studyId, type, columns } = props;
  const [filteredColumns, setFilteredColumns] = useState(columns);
  const { t } = useTranslation();

  const res = usePromise(
    () => getTableMode({ studyId, tableType: type, columns }),
    [studyId, type, columns.join(",")],
  );

  // Filter columns based on the data received, because the API may return
  // fewer columns than requested depending on the study version
  useEffect(
    () => {
      const dataKeys = Object.keys(res.data || {});

      if (dataKeys.length === 0) {
        setFilteredColumns([]);
        return;
      }

      const data = res.data!;
      const dataRowKeys = Object.keys(data[dataKeys[0]]);

      setFilteredColumns(columns.filter((col) => dataRowKeys.includes(col)));
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [res.data, columns.join(",")],
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<TableData>) => {
    return setTableMode({ studyId, tableType: type, data: data.dirtyValues });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={res}
      ifResolved={(data) =>
        filteredColumns.length > 0 ? (
          <TableForm
            defaultValues={data}
            onSubmit={handleSubmit}
            tableProps={{ columns: filteredColumns }}
            autoSubmit={false}
          />
        ) : (
          <EmptyView icon={GridOffIcon} title={t("study.results.noData")} />
        )
      }
    />
  );
}

export default TableMode;
