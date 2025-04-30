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

import { useFormContextPlus } from "@/components/common/Form";
import BooleanFE from "@/components/common/fieldEditors/BooleanFE";
import { TimeSeriesType } from "@/services/api/studies/timeseries/constants";
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { TimeSeriesConfigValues } from "../utils";
import TypeConfigFields from "./TypeConfigFields";

function Fields() {
  const { control } = useFormContextPlus<TimeSeriesConfigValues>();
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TableContainer>
      <Table stickyHeader sx={{ width: "auto" }}>
        <TableHead>
          <TableRow>
            <TableCell />
            <TableCell align="center">{t("global.status")}</TableCell>
            <TableCell align="center">
              {t("study.configuration.tsManagement.numberStochasticTs")}
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody sx={{ "tr:last-child td": { border: "none" } }}>
          {Object.values(TimeSeriesType).map((type) => (
            <TableRow key={type}>
              <TableCell sx={{ fontWeight: "bold" }}>
                {t(`timeSeries.type.${type}`, type)}
              </TableCell>
              <TableCell align="center">
                <BooleanFE
                  name={`${type}.enabled` as const}
                  control={control}
                  trueText={t("study.configuration.tsManagement.status.toBeGenerated")}
                  falseText={t("study.configuration.tsManagement.status.readyMade")}
                  size="extra-small"
                  margin="dense"
                />
              </TableCell>
              <TypeConfigFields type={type} />
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

export default Fields;
