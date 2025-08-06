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
  Tooltip,
  Typography,
} from "@mui/material";
import { useMemo, useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import ConfirmationDialog from "@/components/common/dialogs/ConfirmationDialog";
import PropertiesView from "@/components/common/PropertiesView";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import {
  deleteAdditionalConstraints,
  getAdditionalConstraints,
} from "@/services/api/studies/areas/storages";
import type {
  AdditionalConstraint,
  AdditionalConstraintCreation,
} from "@/services/api/studies/areas/storages/types";
import type { SubmitHandlerPlus } from "@/components/common/Form/types";
import AddConstraintDialog from "./AddConstraintDialog";
import ConstraintDetails from "./ConstraintDetails";

interface Props {
  studyId: string;
  areaId: string;
  storageId: string;
}

function AdditionalConstraints({ studyId, areaId, storageId }: Props) {
  const { t } = useTranslation();
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedConstraintId, setSelectedConstraintId] = useState<string | null>(null);
  const [constraintToDelete, setConstraintToDelete] = useState<string | null>(null);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [constraints, setConstraints] = useState<AdditionalConstraint[]>([]);

  const { data: initialConstraints = [] } = usePromiseWithSnackbarError(
    () => getAdditionalConstraints({ studyId, areaId, storageId }),
    {
      resetDataOnReload: true,
      errorMessage: t("studies.error.retrieveData"),
      deps: [studyId, areaId, storageId],
    },
  );

  useEffect(() => {
    setConstraints(initialConstraints);
  }, [initialConstraints]);

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

  const handleConstraintAdded = (
    _data: SubmitHandlerPlus<AdditionalConstraintCreation>,
    createdConstraints: AdditionalConstraint[],
  ) => {
    setConstraints((prevConstraints) => [...prevConstraints, ...createdConstraints]);

    if (createdConstraints.length > 0) {
      setSelectedConstraintId(createdConstraints[0].id);
    }

    setAddDialogOpen(false);
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
      await deleteAdditionalConstraints({
        studyId,
        areaId,
        storageId,
        constraintIds: [constraintToDelete],
      });

      setConstraints((prevConstraints) =>
        prevConstraints.filter((c) => c.id !== constraintToDelete),
      );

      if (selectedConstraintId === constraintToDelete) {
        setSelectedConstraintId(null);
      }
    } finally {
      setDeleteDialogOpen(false);
      setConstraintToDelete(null);
    }
  };

  const handleConstraintSelect = (constraintId: string) => {
    setSelectedConstraintId(constraintId);
  };

  const handleConstraintUpdated = (
    _data: SubmitHandlerPlus<AdditionalConstraint>,
    updatedConstraints: AdditionalConstraint[],
  ) => {
    setConstraints((prevConstraints) => {
      const updatedMap = new Map(updatedConstraints.map((c) => [c.id, c]));

      return prevConstraints.map((constraint) => {
        const updated = updatedMap.get(constraint.id);
        return updated ?? constraint;
      });
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  const constraintsList = (
    <>
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
              <Tooltip title={constraint.id}>
                <ListItemText
                  primary={constraint.id}
                  sx={{
                    textOverflow: "ellipsis",
                    overflow: "hidden",
                    textWrap: "nowrap",
                  }}
                />
              </Tooltip>
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </>
  );

  return (
    <Box sx={{ display: "flex", height: 1, gap: 1 }}>
      {/* Left panel - Constraints list */}
      <Box sx={{ width: 250 }}>
        <PropertiesView
          onSearchFilterChange={handleSearchChange}
          onAdd={() => setAddDialogOpen(true)}
          mainContent={constraintsList}
        />
      </Box>

      {/* Right panel - Constraint details */}
      <Box sx={{ flex: 1, p: 2 }}>
        {selectedConstraint ? (
          <ConstraintDetails
            studyId={studyId}
            areaId={areaId}
            storageId={storageId}
            constraint={selectedConstraint}
            onUpdate={handleConstraintUpdated}
          />
        ) : (
          <Box
            sx={{
              height: 1,
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
      </Box>

      {/* Dialogs */}
      <AddConstraintDialog
        open={addDialogOpen}
        onClose={() => setAddDialogOpen(false)}
        onSave={handleConstraintAdded}
        studyId={studyId}
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
