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

import { capitalize } from "lodash";
import * as R from "ramda";

import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@mui/material";

import CheckBoxFE from "@/components/common/fieldEditors/CheckBoxFE";
import NumberFE from "@/components/common/fieldEditors/NumberFE";
import SelectFE from "@/components/common/fieldEditors/SelectFE";
import SwitchFE from "@/components/common/fieldEditors/SwitchFE";
import { useFormContextPlus } from "@/components/common/Form";

import { SEASONAL_CORRELATION_OPTIONS, TSFormFields, TSType } from "./utils";

const borderStyle = "1px solid rgba(255, 255, 255, 0.12)";

function Fields() {
  const { control, getValues, setValue } = useFormContextPlus<TSFormFields>();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TableContainer>
      <Table sx={{ minWidth: "1050px" }} size="small">
        <TableHead>
          <TableRow sx={{ th: { py: 1, borderBottom: "none" } }}>
            <TableCell />
            <TableCell sx={{ borderRight: borderStyle }} align="center">
              Ready made TS
            </TableCell>
            <TableCell
              sx={{ borderRight: borderStyle }}
              align="center"
              colSpan={7}
            >
              Stochastic TS
            </TableCell>
            <TableCell align="center" colSpan={2}>
              Draw correlation
            </TableCell>
          </TableRow>
          <TableRow
            sx={{
              th: {
                fontWeight: "bold",
                borderBottom: borderStyle,
              },
            }}
          >
            <TableCell />
            <TableCell align="center">Status</TableCell>
            <TableCell align="center">Status</TableCell>
            <TableCell align="center">Number</TableCell>
            <TableCell align="center">Refresh</TableCell>
            <TableCell align="center">Refresh interval</TableCell>
            <TableCell align="center">Season correlation</TableCell>
            <TableCell align="center">Store in input</TableCell>
            <TableCell align="center">Store in output</TableCell>
            <TableCell align="center">Intra-modal</TableCell>
            <TableCell align="center">inter-modal</TableCell>
          </TableRow>
        </TableHead>
        <TableBody
          sx={{
            "th, td": { borderBottom: borderStyle },
          }}
        >
          {R.values(TSType)
            .filter((type) => !!getValues(type))
            .map((type) => {
              const isSpecialType =
                type === TSType.Renewables || type === TSType.NTC;
              const emptyDisplay = "-";
              const notApplicableDisplay = "n/a";
              const isReadyMadeStatusEnable = !getValues(
                `${type}.stochasticTsStatus`,
              );

              const ifNotSpecialType = (
                fn: (
                  t: Exclude<TSType, TSType.Renewables | TSType.NTC>,
                ) => React.ReactNode,
              ) => {
                return isSpecialType ? emptyDisplay : fn(type);
              };

              return (
                <TableRow key={type}>
                  <TableCell sx={{ fontWeight: "bold" }}>
                    {capitalize(type)}
                  </TableCell>
                  <TableCell align="center">
                    <SwitchFE
                      value={isReadyMadeStatusEnable}
                      onChange={(_, checked) => {
                        setValue(
                          `${type}.stochasticTsStatus`,
                          !checked as never,
                        );
                      }}
                    />
                  </TableCell>
                  <TableCell align="center">
                    <SwitchFE
                      name={`${type}.stochasticTsStatus` as const}
                      control={control}
                    />
                  </TableCell>
                  <TableCell align="center">
                    {ifNotSpecialType((t) => (
                      <NumberFE
                        name={`${t}.number` as const}
                        control={control}
                        size="small"
                        fullWidth
                        disabled={isReadyMadeStatusEnable}
                      />
                    ))}
                  </TableCell>
                  <TableCell align="center">
                    {ifNotSpecialType((t) => (
                      <CheckBoxFE
                        name={`${t}.refresh` as const}
                        control={control}
                        disabled={isReadyMadeStatusEnable}
                      />
                    ))}
                  </TableCell>
                  <TableCell align="center">
                    {ifNotSpecialType((t) => (
                      <NumberFE
                        name={`${t}.refreshInterval` as const}
                        control={control}
                        size="small"
                        fullWidth
                        disabled={isReadyMadeStatusEnable}
                      />
                    ))}
                  </TableCell>
                  <TableCell align="center">
                    {ifNotSpecialType((t) =>
                      t !== TSType.Thermal ? (
                        <SelectFE
                          name={`${t}.seasonCorrelation` as const}
                          options={SEASONAL_CORRELATION_OPTIONS}
                          control={control}
                          size="small"
                          disabled={isReadyMadeStatusEnable}
                        />
                      ) : (
                        notApplicableDisplay
                      ),
                    )}
                  </TableCell>
                  <TableCell align="center">
                    {ifNotSpecialType((t) => (
                      <CheckBoxFE
                        name={`${t}.storeInInput` as const}
                        control={control}
                        disabled={isReadyMadeStatusEnable}
                      />
                    ))}
                  </TableCell>
                  <TableCell align="center">
                    {ifNotSpecialType((t) => (
                      <CheckBoxFE
                        name={`${t}.storeInOutput` as const}
                        control={control}
                        disabled={isReadyMadeStatusEnable}
                      />
                    ))}
                  </TableCell>
                  <TableCell align="center">
                    <CheckBoxFE
                      name={`${type}.intraModal` as const}
                      control={control}
                    />
                  </TableCell>
                  <TableCell align="center">
                    {type !== TSType.NTC ? (
                      <CheckBoxFE
                        name={`${type}.interModal` as const}
                        control={control}
                      />
                    ) : (
                      emptyDisplay
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

export default Fields;
