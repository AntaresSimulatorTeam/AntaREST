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

import FormDialog from "@/components/common/dialogs/FormDialog";
import NumberFE from "@/components/common/fieldEditors/NumberFE";
import { default as RadioGroupFE } from "@/components/common/fieldEditors/RadioGroupFE";
import StringFE from "@/components/common/fieldEditors/StringFE";
import type { SubmitHandlerPlus } from "@/components/common/Form/types";
import { setValueAsNumber } from "@/utils/reactHookFormUtils";
import { validateNumber } from "@/utils/validation/number";
import { Box, Tooltip, setRef } from "@mui/material";
import * as R from "ramda";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  type Range,
  SELECTIONS_SEPARATOR,
  type Selection,
  type SelectionType,
  isSelectionValid,
  selectionsToNumbers,
  selectionsToString,
  stringToSelection,
} from "./utils";

interface Props {
  valueRef: React.MutableRefObject<Selection[]>;
  maxYears: number;
}

function YearsSelectionFE({ valueRef, maxYears }: Props) {
  const [openSelectionDialog, setOpenSelectionDialog] = useState(false);
  const [selections, setSelections] = useState<Selection[]>([]);
  const { t } = useTranslation();
  const selectionString = selectionsToString(selections);

  const defaultValues = useMemo(() => {
    const selectionType: SelectionType =
      selections.length === 0
        ? "all"
        : selections.length === 1 && Array.isArray(selections[0])
          ? "range"
          : "advanced";

    return {
      type: selectionType,
      range:
        selectionType === "range"
          ? R.zipObj(["start", "end"], selections[0] as Range)
          : { start: 1, end: 1 },
      advanced: selectionType === "advanced" ? selectionsToString(selections) : "",
    };
  }, [selections]);

  useEffect(() => {
    setRef(valueRef, selectionsToNumbers(selections));
  }, [selections, valueRef]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({
    values: { type, range, advanced },
  }: SubmitHandlerPlus<typeof defaultValues>) => {
    const newSelection: Selection[] = [];

    if (type === "range") {
      newSelection.push([range.start, range.end]);
    } else if (type === "advanced") {
      newSelection.push(...stringToSelection(advanced));
    }

    setSelections(newSelection);
    setOpenSelectionDialog(false);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Tooltip title={selectionString} placement="top" disableFocusListener>
        <span>
          <StringFE
            label={t("global.years")}
            value={selectionString || t("global.all")}
            slotProps={{ input: { readOnly: true } }}
            sx={{ input: { cursor: "pointer" } }}
            onClick={() => setOpenSelectionDialog(true)}
            size="extra-small"
          />
        </span>
      </Tooltip>
      <FormDialog
        open={openSelectionDialog}
        title={t("global.years")}
        submitButtonIcon={null}
        submitButtonText={t("global.validate")}
        config={{ defaultValues }}
        onSubmit={handleSubmit}
        allowSubmitOnPristine
        onCancel={() => setOpenSelectionDialog(false)}
      >
        {({ control, watch, setValue }) => {
          const [currentType, currentRange] = watch(["type", "range"]);

          return (
            <>
              <RadioGroupFE
                name="type"
                control={control}
                fullWidth
                radios={[
                  { value: "all", label: t("global.all") },
                  {
                    value: "range",
                    label: (
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1, py: 2 }}>
                        {t("global.from")}
                        <NumberFE
                          name="range.start"
                          control={control}
                          size="extra-small"
                          sx={{ width: "min-content" }}
                          rules={{
                            deps: "range.end",
                            setValueAs: setValueAsNumber({ min: 1, max: maxYears }),
                            onChange: (event) => {
                              if (event.target.value > currentRange.end) {
                                setValue("range.end", event.target.value);
                              }
                            },
                            validate: (v, { type }) => {
                              if (type === "range") {
                                return validateNumber(v, {
                                  min: 1,
                                  max: maxYears,
                                });
                              }
                            },
                          }}
                          disabled={currentType !== "range"}
                        />
                        {t("global.to").toLowerCase()}
                        <NumberFE
                          name="range.end"
                          control={control}
                          size="extra-small"
                          sx={{ width: "min-content" }}
                          rules={{
                            deps: "range.start",
                            setValueAs: setValueAsNumber({ min: 1, max: maxYears }),
                            onChange: (event) => {
                              if (event.target.value < currentRange.start) {
                                setValue("range.start", event.target.value);
                              }
                            },
                            validate: (v, { type, range }) => {
                              if (type === "range") {
                                return validateNumber(v, {
                                  min: Math.min(range.start, maxYears),
                                  max: maxYears,
                                });
                              }
                            },
                          }}
                          disabled={currentType !== "range"}
                        />
                      </Box>
                    ),
                  },
                  {
                    value: "advanced",
                    label: (
                      <StringFE
                        name="advanced"
                        control={control}
                        size="extra-small"
                        multiline
                        fullWidth
                        placeholder={t(
                          "study.configuration.general.mcScenarioPlaylist.yearsSelection.advanced.placeholder",
                        )}
                        rules={{
                          validate: (v, { type }) => {
                            if (type === "advanced") {
                              if (!v) {
                                return t("form.field.required");
                              }
                              return (
                                R.all(
                                  (str) => isSelectionValid(str, maxYears),
                                  v.split(SELECTIONS_SEPARATOR).filter(Boolean),
                                ) ||
                                t(
                                  "study.configuration.general.mcScenarioPlaylist.yearsSelection.advanced.error",
                                )
                              );
                            }
                          },
                        }}
                        disabled={currentType !== "advanced"}
                      />
                    ),
                  },
                ]}
              />
            </>
          );
        }}
      </FormDialog>
    </>
  );
}

export default YearsSelectionFE;
