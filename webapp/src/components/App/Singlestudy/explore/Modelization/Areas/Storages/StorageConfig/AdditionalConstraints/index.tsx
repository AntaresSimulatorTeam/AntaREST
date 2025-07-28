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

import { Delete as DeleteIcon } from "@mui/icons-material";
import {
  Box,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Paper,
  Typography,
} from "@mui/material";
import { useSnackbar } from "notistack";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import ConfirmationDialog from "@/components/common/dialogs/ConfirmationDialog";
import PropertiesView from "@/components/common/PropertiesView";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import type { StudyMetadata } from "@/types/types";
import AddConstraintDialog from "./AddConstraintDialog";
import ConstraintDetails from "./ConstraintDetails";
import { deleteAdditionalConstraint, getAdditionalConstraints } from "./utils";

interface Props {
  study: StudyMetadata;
  areaId: string;
  storageId: string;
}

function AdditionalConstraints({ study, areaId, storageId }: Props) {
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedConstraintId, setSelectedConstraintId] = useState<string | null>(null);
  const [constraintToDelete, setConstraintToDelete] = useState<string | null>(null);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const { data: constraints = [], reload } = usePromiseWithSnackbarError(
    () => getAdditionalConstraints(study.id, areaId, storageId),
    {
      resetDataOnReload: true,
      errorMessage: t("studies.error.retrieveData"),
      deps: [study.id, areaId, storageId],
    },
  );

  const filteredConstraints = useMemo(() => {
    if (!searchTerm) {
      return constraints;
    }

    return constraints.filter((constraint) => constraint.id.includes(searchTerm.toLowerCase()));
  }, [constraints, searchTerm]);

  const selectedConstraint = useMemo(() => {
    if (!selectedConstraintId) {
      return null;
    }

    return constraints.find((c) => c.id === selectedConstraintId);
  }, [constraints, selectedConstraintId]);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
  };

  const handleAddConstraint = () => {
    setAddDialogOpen(true);
  };

  const handleConstraintAdded = () => {
    setAddDialogOpen(false);
    enqueueSnackbar(t("study.modelization.storages.additionalConstraints.createSuccess"), {
      variant: "success",
    });
    reload();
  };

  const handleDeleteClick = (constraintId: string) => {
    setConstraintToDelete(constraintId);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!constraintToDelete) {
      return;
    }

    try {
      await deleteAdditionalConstraint(study.id, areaId, constraintToDelete);

      if (selectedConstraintId === constraintToDelete) {
        setSelectedConstraintId(null);
      }

      reload();
    } finally {
      setDeleteDialogOpen(false);
      setConstraintToDelete(null);
    }
  };

  const handleConstraintSelect = (constraintId: string) => {
    setSelectedConstraintId(constraintId);
  };

  const handleConstraintUpdated = () => {
    reload();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  const constraintsList = (
    <>
      <Typography variant="subtitle2" sx={{ px: 1, mb: 1 }}>
        {t("study.modelization.storages.additionalConstraints.list")} ({filteredConstraints.length})
      </Typography>
      <List sx={{ overflow: "auto" }}>
        {filteredConstraints.map((constraint) => (
          <ListItem
            key={constraint.id}
            secondaryAction={
              <IconButton
                edge="end"
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteClick(constraint.id);
                }}
              >
                <DeleteIcon />
              </IconButton>
            }
            disablePadding
          >
            <ListItemButton
              selected={selectedConstraintId === constraint.id}
              onClick={() => handleConstraintSelect(constraint.id)}
            >
              <ListItemText primary={constraint.id} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </>
  );

  return (
    <Box sx={{ display: "flex", height: "100%", gap: 1 }}>
      {/* Left panel - Constraints list */}
      <Paper sx={{ width: 250 }} elevation={2}>
        <PropertiesView
          onSearchFilterChange={handleSearchChange}
          onAdd={handleAddConstraint}
          mainContent={constraintsList}
        />
      </Paper>

      {/* Right panel - Constraint details */}
      <Paper sx={{ flex: 1, p: 2 }} elevation={3}>
        {selectedConstraint ? (
          <ConstraintDetails
            study={study}
            areaId={areaId}
            storageId={storageId}
            constraint={selectedConstraint}
            onUpdate={handleConstraintUpdated}
          />
        ) : (
          <Box
            sx={{
              height: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Typography color="text.secondary">
              {t("study.modelization.storages.additionalConstraints.selectConstraint")}
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Dialogs */}
      <AddConstraintDialog
        open={addDialogOpen}
        onClose={() => setAddDialogOpen(false)}
        onSave={handleConstraintAdded}
        study={study}
        areaId={areaId}
        storageId={storageId}
      />

      <ConfirmationDialog
        open={deleteDialogOpen}
        onCancel={() => setDeleteDialogOpen(false)}
        onConfirm={handleDeleteConfirm}
        alert="warning"
        titleIcon={DeleteIcon}
      >
        {t("study.modelization.storages.additionalConstraints.confirmDelete")}
      </ConfirmationDialog>
    </Box>
  );
}

export default AdditionalConstraints;
