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

import LinearProgressWithLabel from "@/components/LinearProgressWithLabel";
import useDialog from "@/hooks/useDialog";
import { tableModeCreationSchema } from "@/services/api/tablemode/schemas";
import type { TableModeCreation } from "@/services/api/tablemode/types";
import storage from "@/services/utils/localStorage";
import { appendColon } from "@/utils/i18nUtils";
import { buildKey } from "@/utils/reactUtils";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import {
  Backdrop,
  Box,
  Button,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Paper,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import axios, { AxiosError } from "axios";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useMount } from "react-use";
import useCreateTableMode from "../../-hooks/useCreateTableMode";

interface MigrationState {
  status: "disabled" | "loading" | "success" | "error";
  migrated: number;
  failed: Array<[TableModeCreation, AxiosError | undefined]>;
  total: number;
}

const DEFAULT_MIGRATION_STATE: MigrationState = {
  status: "disabled",
  migrated: 0,
  failed: [],
  total: 0,
} as const;

const LOCAL_STORAGE_KEY = "studies.model.tableMode.templates" as const;

/**
 * Workaround to migrate table modes stored in localStorage to the new backend system (since v2.32.0).
 * It can be removed after a certain period of time when we are confident that most users have migrated.
 */

function MigrationTableModes() {
  const createTableMode = useCreateTableMode({ notifyError: false });
  const { t } = useTranslation();
  const [state, setState] = useState<MigrationState>(DEFAULT_MIGRATION_STATE);
  const { confirm } = useDialog();

  useMount(migrateTableModes);

  ////////////////////////////////////////////////////////////////
  // Functions
  ////////////////////////////////////////////////////////////////

  async function migrateTableModes() {
    const oldTableModes = storage.getItem(LOCAL_STORAGE_KEY);

    // Invalid data or no data to migrate
    if (!Array.isArray(oldTableModes) || oldTableModes.length === 0) {
      storage.removeItem(LOCAL_STORAGE_KEY);
      return;
    }

    setState({
      ...DEFAULT_MIGRATION_STATE,
      status: "loading",
      total: oldTableModes.length,
    });

    const failed: MigrationState["failed"] = [];

    for (const value of oldTableModes) {
      // Ignore invalid table modes
      if (!tableModeCreationSchema.safeParse(value).success) {
        continue;
      }

      try {
        await createTableMode.mutateAsync(value);
        setState((prev) => ({ ...prev, migrated: prev.migrated + 1 }));
      } catch (err) {
        failed.push([value, axios.isAxiosError(err) ? err : undefined]);
      }
    }

    // If all table modes have been migrated successfully, we can remove the localStorage key
    if (failed.length === 0) {
      storage.removeItem(LOCAL_STORAGE_KEY);
    }
    // If some table modes failed to migrate, we keep them in localStorage to retry later
    else {
      storage.setItem(
        LOCAL_STORAGE_KEY,
        failed.map(([tableModeCreation]) => tableModeCreation),
      );
    }

    setState(prev => ({
      ...prev,
      status: failed.length > 0 ? "error" : "success",
      failed,
      total: oldTableModes.length,
    }));
  }

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDelete = async () => {
    const isConfirmed = await confirm({
      content: t("study.tableModes.migration.deleteConfirm"),
      alert: "error",
    });

    if (isConfirmed) {
      storage.removeItem(LOCAL_STORAGE_KEY);
      setState(DEFAULT_MIGRATION_STATE);
    }
  };

  const handleClose = async () => {
    if (state.status === "success") {
      setState(DEFAULT_MIGRATION_STATE);
      return;
    }

    const isConfirmed = await confirm({
      content: t("study.tableModes.migration.closeConfirm"),
      alert: "warning",
    });

    if (isConfirmed) {
      setState(DEFAULT_MIGRATION_STATE);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (state.status === "disabled") {
    return null;
  }

  return (
    <Backdrop open sx={{ position: "absolute" }}>
      <Paper
        sx={{
          display: "flex",
          flexDirection: "column",
          gap: 1,
        }}
      >
        <Box sx={{ p: 2 }}>
          <Typography variant="h6">{t("study.tableModes.migration.title")}</Typography>
          {/* Loading */}
          {state.status === "loading" && (
            <LinearProgressWithLabel value={(state.migrated / state.total) * 100} />
          )}
          {/* Error */}
          {state.status === "error" && (
            <>
              <Typography variant="body2" color="error" sx={{ mt: 1 }}>
                {t("study.tableModes.migration.error", { count: state.failed.length })}
              </Typography>
              <List dense sx={{ overflow: "auto" }}>
                {state.failed.map(([tableModeCreation, error], index) => (
                  <ListItem
                    key={buildKey(tableModeCreation.name, index)}
                    secondaryAction={
                      <Tooltip
                        title={`${appendColon(t("global.columns"))} ${tableModeCreation.columns.join(", ")}`}
                      >
                        <IconButton edge="end">
                          <InfoOutlinedIcon />
                        </IconButton>
                      </Tooltip>
                    }
                  >
                    <ListItemText primary={tableModeCreation.name} secondary={error?.message} />
                  </ListItem>
                ))}
              </List>
            </>
          )}
          {/* Success */}
          {state.status === "success" && (
            <Typography variant="body2" color="success.main" sx={{ mt: 1 }}>
              {t("study.tableModes.migration.success", { count: state.migrated })}
            </Typography>
          )}
        </Box>
        <Stack justifyContent="flex-end" spacing={1} sx={{ p: 1 }}>
          {state.status === "error" && (
            <>
              <Button variant="contained" color="secondary" onClick={migrateTableModes}>
                {t("global.retry")}
              </Button>
              <Button variant="contained" color="error" onClick={handleDelete}>
                {t("global.delete")}
              </Button>
            </>
          )}
          <Button disabled={state.status === "loading"} onClick={handleClose}>
            {t("global.close")}
          </Button>
        </Stack>
      </Paper>
    </Backdrop>
  );
}

export default MigrationTableModes;
