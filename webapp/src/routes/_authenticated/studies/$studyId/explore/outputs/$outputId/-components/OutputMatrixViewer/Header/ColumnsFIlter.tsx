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

import CheckboxesTagsFE from "@/components/fieldEditors/CheckboxesTagsFE";
import Fieldset from "@/components/Fieldset";
import Form from "@/components/Form";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import ViewColumnIcon from "@mui/icons-material/ViewColumn";
import { Box, Button, Drawer, Toolbar, Typography } from "@mui/material";
import { useId } from "react";
import { useTranslation } from "react-i18next";
import useOutputFilters from "../../../-hooks/useOutputFilters";
import type { ColumnsInfo } from "../utils";

interface Props {
  open: boolean;
  onClose: VoidFunction;
}

function ColumnsFilter({ open, onClose }: Props) {
  const { setColumnsSearch, columnsSearch, columnsData } = useOutputFilters();
  const { t } = useTranslation();
  const formId = useId();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values }: SubmitHandlerPlus<ColumnsInfo>) => {
    setColumnsSearch(values);
  };

  const handleReset = () => {
    setColumnsSearch({
      variables: [],
      units: [],
      stats: [],
    });

    onClose();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Drawer
      open={open}
      onClose={onClose}
      anchor="right"
      sx={{ left: "unset" }}
      slotProps={{
        paper: { sx: { width: 300 } },
        // hideBackdrop={true} removes the backdrop DOM element entirely,
        // eliminating the click target that triggers `onClose`.
        // Using transparent backdrop preserves the invisible click target
        // for pointer events while removing the visual overlay.
        backdrop: {
          sx: {
            backgroundColor: "transparent",
          },
        },
      }}
    >
      <Toolbar>
        <ViewColumnIcon sx={{ mr: 1 }} />
        <Typography variant="h6">Filter Columns</Typography>
      </Toolbar>
      <Form
        config={{ defaultValues: columnsSearch }}
        id={formId}
        onSubmit={handleSubmit}
        onSubmitSuccessful={onClose}
        sx={{ p: 2 }}
        hideSubmitButton
      >
        {({ control }) => (
          <>
            <Fieldset fullFieldWidth>
              <CheckboxesTagsFE
                name="variables"
                label="Variables"
                control={control}
                options={columnsData.variables}
                freeSolo
              />
              <CheckboxesTagsFE
                name="units"
                label="Units"
                control={control}
                options={columnsData.units}
                freeSolo
              />
              <CheckboxesTagsFE
                name="stats"
                label="Stats"
                control={control}
                options={columnsData.stats}
                freeSolo
              />
            </Fieldset>
          </>
        )}
      </Form>
      <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 1, p: 1 }}>
        <Button variant="outlined" onClick={handleReset}>
          {t("global.reset")}
        </Button>
        <Button variant="contained" type="submit" form={formId}>
          {t("global.filterAction")}
        </Button>
      </Box>
    </Drawer>
  );
}

export default ColumnsFilter;
