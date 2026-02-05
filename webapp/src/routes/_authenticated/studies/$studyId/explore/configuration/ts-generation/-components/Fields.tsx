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

import SwitchFE from "@/components/fieldEditors/SwitchFE";
import { useFormContextPlus } from "@/hooks/useFormContextPlus";
import { TimeSeriesType } from "@/services/api/studies/timeseries/constants";
import BuildIcon from "@mui/icons-material/Build";
import {
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import type { TimeSeriesConfigValues } from "../-utils";
import TypeConfigFields from "./TypeConfigFields";

function Fields() {
  const {
    control,
    formState: { errors },
  } = useFormContextPlus<TimeSeriesConfigValues>();
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
            <TableCell align="center">
              {t("study.configuration.tsManagement.numberStochasticTs")}
            </TableCell>
            <TableCell align="center">
              {t("study.configuration.tsManagement.thermalOutageDetails")}
            </TableCell>
            <TableCell />
          </TableRow>
        </TableHead>
        <TableBody sx={{ "tr:last-child > *": { border: "none" } }}>
          {Object.values(TimeSeriesType).map((type) => (
            <TableRow key={type}>
              <TableCell sx={{ fontWeight: "bold" }} component="th" scope="row">
                {t(`timeSeries.type.${type}`, type)}
              </TableCell>
              <TypeConfigFields type={type} />
              <TableCell align="center">
                {type === TimeSeriesType.Thermal ? (
                  <SwitchFE
                    name={`${type}.outageDetails` as const}
                    control={control}
                    size="medium"
                  />
                ) : null}
              </TableCell>
              <TableCell>
                {/* ⚠️ When there will be more than one type, this button must be specific to each type */}
                <Button
                  variant="contained"
                  startIcon={<BuildIcon fontSize="extra-small" />}
                  size="extra-small"
                  type="submit"
                  disabled={!!errors[type]}
                >
                  {t("study.configuration.tsManagement.generateTs")}
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

export default Fields;
