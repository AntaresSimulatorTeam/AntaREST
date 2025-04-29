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
import { validateNumber } from "@/utils/validation/number";
import { Box, Tooltip } from "@mui/material";
import * as R from "ramda";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  type Range,
  type Selection,
  type SelectionType,
  isSelectionValid,
  selectionsToString,
  stringToSelection,
} from "./utils";

function YearsSelectionFE() {
  const [openSelectionDialog, setOpenSelectionDialog] = useState(false);
  const [selections, setSelections] = useState<Selection[]>([]);
  const { t } = useTranslation();
  const selectionString = selectionsToString(selections, " • ");

  const defaultValues = useMemo(() => {
    const selectionType: SelectionType =
      selections.length === 0
        ? "all"
        : selections.length === 1 && Array.isArray(selections[0])
          ? "range"
          : "advancedRange";

    return {
      type: selectionType,
      range:
        selectionType === "range"
          ? R.zipObj(["start", "end"], selections[0] as Range)
          : { start: 1, end: 1 },
      advancedRange: selectionType === "advancedRange" ? selectionsToString(selections) : "",
    };
  }, [selections]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({
    values: { type, range, advancedRange },
  }: SubmitHandlerPlus<typeof defaultValues>) => {
    const newSelection: Selection[] = [];

    if (type === "range") {
      newSelection.push([range.start, range.end]);
    } else if (type === "advancedRange") {
      newSelection.push(...stringToSelection(advancedRange));
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
        <StringFE
          label={t("global.years")}
          value={selectionString || t("global.all")}
          slotProps={{ input: { readOnly: true } }}
          sx={{ input: { cursor: "pointer" } }}
          onClick={() => setOpenSelectionDialog(true)}
          size="extra-small"
          margin="dense"
        />
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
        {({ control, watch }) => {
          const currentType = watch("type");

          return (
            <>
              <RadioGroupFE
                name="type"
                control={control}
                radios={[
                  { value: "all", label: t("global.all") },
                  {
                    value: "range",
                    label: (
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1, py: 2 }}>
                        Range from
                        <NumberFE
                          name="range.start"
                          control={control}
                          size="extra-small"
                          sx={{ width: "min-content" }}
                          rules={{
                            deps: "range.end",
                            validate: (v, { type, range }) => {
                              if (type === "range") {
                                return validateNumber(v, {
                                  min: 1,
                                  max: range.end,
                                });
                              }
                            },
                          }}
                          disabled={currentType !== "range"}
                        />
                        to
                        <NumberFE
                          name="range.end"
                          control={control}
                          size="extra-small"
                          sx={{ width: "min-content" }}
                          rules={{
                            deps: "range.start",
                            validate: (v, { type, range }) => {
                              if (type === "range") {
                                return validateNumber(v, {
                                  min: Math.max(range.start, 1),
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
                    value: "advancedRange",
                    label: (
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                        Advanced Range:
                        <StringFE
                          name="advancedRange"
                          control={control}
                          size="extra-small"
                          multiline
                          minRows={2}
                          maxRows={4}
                          rules={{
                            validate: (v, { type }) => {
                              if (type === "advancedRange") {
                                if (!v) {
                                  return t("form.field.required");
                                }
                                return (
                                  R.all(isSelectionValid, v.split(/\n/).filter(Boolean)) ||
                                  "Invalid range"
                                );
                              }
                            },
                          }}
                          disabled={currentType !== "advancedRange"}
                        />
                      </Box>
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
