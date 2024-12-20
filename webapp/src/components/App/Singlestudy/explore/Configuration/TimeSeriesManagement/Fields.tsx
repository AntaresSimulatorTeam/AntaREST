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

import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@mui/material";
import { capitalize } from "lodash";
import NumberFE from "../../../../../common/fieldEditors/NumberFE";
import { useFormContextPlus } from "../../../../../common/Form";
import { TSFormFields, TSType } from "./utils";
import BooleanFE from "../../../../../common/fieldEditors/BooleanFE";
import { useTranslation } from "react-i18next";
import { validateNumber } from "@/utils/validation/number";

const borderStyle = "1px solid rgba(255, 255, 255, 0.12)";

function Fields() {
  const { control, watch } = useFormContextPlus<TSFormFields>();
  const isReadyMade = watch("thermal.stochasticTsStatus") === false;
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TableContainer>
      <Table size="small" sx={{ width: "auto" }}>
        <TableHead>
          <TableRow
            sx={{
              th: {
                fontWeight: "bold",
                borderBottom: borderStyle,
              },
            }}
          >
            <TableCell />
            <TableCell align="center">{t("global.status")}</TableCell>
            <TableCell align="center">
              {t("study.configuration.tsManagement.numberStochasticTs")}
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody
          sx={{
            "th, td": { borderBottom: borderStyle },
            "tr:last-child td": {
              borderBottomColor: "transparent", // 'border: none' change the color of `TableHead` border
            },
          }}
        >
          <TableRow>
            <TableCell sx={{ fontWeight: "bold" }}>
              {capitalize(TSType.Thermal)}
            </TableCell>
            <TableCell align="center">
              <BooleanFE
                name={"thermal.stochasticTsStatus"}
                control={control}
                trueText={t(
                  "study.configuration.tsManagement.status.toBeGenerated",
                )}
                falseText={t(
                  "study.configuration.tsManagement.status.readyMade",
                )}
                variant="outlined"
                size="small"
              />
            </TableCell>
            <TableCell align="center">
              <NumberFE
                name={"thermal.number"}
                control={control}
                size="small"
                disabled={isReadyMade}
                rules={{ validate: validateNumber({ min: 1 }) }}
                sx={{ width: 110 }}
              />
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  );
}

export default Fields;
