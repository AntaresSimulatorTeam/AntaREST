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

import FieldSkeleton from "@/components/fieldEditors/FieldSkeleton";
import type {
  AdditionalConstraint,
  AdditionalConstraintOccurrences,
} from "@/services/api/studies/areas/storages/types";
import { compactSelections, selectionToString } from "@/utils/numberSelectionsUtils";
import { buildKey } from "@/utils/reactUtils";
import EditIcon from "@mui/icons-material/Edit";
import {
  Box,
  Button,
  Chip,
  FormHelperText,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Typography,
} from "@mui/material";
import { useController, type Control } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { useToggle } from "react-use";
import OccurrencesTableDialog from "./OccurrencesTableDialog";
import { validateOccurrences } from "./utils";

interface Props {
  control: Control<AdditionalConstraint>;
  onChange: (occurrences: AdditionalConstraintOccurrences) => void;
}

function OccurrencesFE({ control, onChange }: Props) {
  const { t } = useTranslation();
  const [openEditDialog, toggleEditDialog] = useToggle(false);

  const {
    field,
    formState: { isLoading },
    fieldState: { invalid, error },
  } = useController({
    name: "occurrences",
    control,
    defaultValue: [],
    rules: { validate: validateOccurrences },
  });

  const occurrences = field.value;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = (newOccurrences: AdditionalConstraintOccurrences) => {
    field.onChange(newOccurrences);
    onChange(newOccurrences);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <FieldSkeleton isLoading={isLoading}>
        <Paper elevation={3} sx={[invalid && { border: "1px solid", borderColor: "error.main" }]}>
          <Box sx={{ display: "flex", alignItems: "center", p: 1 }}>
            <Typography color="textSecondary" sx={{ flex: 1 }}>
              {t("study.modeling.storages.additionalConstraints.occurrences")}
            </Typography>
            <Button startIcon={<EditIcon />} onClick={toggleEditDialog}>
              {t("global.edit")}
            </Button>
          </Box>
          <TableContainer>
            <Table>
              <TableBody sx={{ "tr:last-child > *": { border: "none" } }}>
                {occurrences.map(({ hours }, index) => (
                  <TableRow key={buildKey(hours, index)}>
                    <TableCell
                      sx={{
                        fontWeight: "bold",
                        position: "sticky",
                        left: 0,
                        bgcolor: "background.paper",
                        width: 0, // Adapt width to content
                      }}
                      component="th"
                      scope="row"
                    >
                      {index + 1}
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: "flex", gap: 0.5 }}>
                        {compactSelections(hours).map((selection) => (
                          <Chip
                            key={String(selection)}
                            label={selectionToString(selection)}
                            sx={{ borderRadius: 1 }}
                          />
                        ))}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
        {invalid && (
          <FormHelperText error sx={{ mx: 2 }}>
            {error?.message}
          </FormHelperText>
        )}
      </FieldSkeleton>
      {openEditDialog && (
        <OccurrencesTableDialog
          open
          onClose={toggleEditDialog}
          control={control}
          occurrences={occurrences}
          onEdit={handleChange}
        />
      )}
    </>
  );
}

export default OccurrencesFE;
