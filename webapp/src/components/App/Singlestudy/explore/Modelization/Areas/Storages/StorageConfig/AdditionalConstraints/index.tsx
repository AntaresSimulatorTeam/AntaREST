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

import ConfirmationDialog from "@/components/common/dialogs/ConfirmationDialog";
import SimpleLoader from "@/components/common/loaders/SimpleLoader";
import EmptyView from "@/components/common/page/EmptyView";
import ViewWrapper from "@/components/common/page/ViewWrapper";
import PropertiesView from "@/components/common/PropertiesView";
import SplitView from "@/components/common/SplitView";
import useConfirm from "@/hooks/useConfirm";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import {
  deleteAdditionalConstraints,
  getAdditionalConstraints,
} from "@/services/api/studies/areas/storages";
import type { AdditionalConstraint } from "@/services/api/studies/areas/storages/types";
import { sortByName } from "@/services/utils";
import { toError } from "@/utils/fnUtils";
import { isSearchMatching } from "@/utils/stringUtils";
import { Delete as DeleteIcon } from "@mui/icons-material";
import { Box, List, ListItem, ListItemButton, ListItemText, Tooltip } from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import AddConstraintDialog from "./AddConstraintDialog";
import ConstraintForm from "./ConstraintForm";

interface Props {
  studyId: string;
  areaId: string;
  storageId: string;
}

function AdditionalConstraints({ studyId, areaId, storageId }: Props) {
  const { t } = useTranslation();
  const [searchValue, setSearchValue] = useState("");
  const [constraints, setConstraints] = useState<AdditionalConstraint[]>([]);
  const [selectedConstraintId, setSelectedConstraintId] = useState<string | null>(null);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const deleteAction = useConfirm<{ name: string }>();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const { isLoading, isRejected, error } = usePromiseWithSnackbarError(
    () => getAdditionalConstraints({ studyId, areaId, storageId }),
    {
      onDataChange: (data = []) => setConstraints(data),
      errorMessage: t("studies.error.retrieveData"),
      deps: [studyId, areaId, storageId],
    },
  );

  const filteredAndSortedConstraints = useMemo(() => {
    const filteredConstraints = searchValue
      ? constraints.filter(({ name }) => isSearchMatching(searchValue, name))
      : constraints;

    return sortByName(filteredConstraints);
  }, [constraints, searchValue]);

  // Reset selected constraint ID if the current one is not valid
  useEffect(() => {
    if (
      selectedConstraintId === null ||
      !constraints.find(({ id }) => id === selectedConstraintId)
    ) {
      const firstVisibleConstraint = filteredAndSortedConstraints[0];
      setSelectedConstraintId(firstVisibleConstraint?.id || null);
    }
  }, [constraints, filteredAndSortedConstraints, selectedConstraintId]);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleAdd = (createdConstraint: AdditionalConstraint) => {
    setConstraints((prevConstraints) => [...prevConstraints, createdConstraint]);
    setSelectedConstraintId(createdConstraint.id);
  };

  const handleDelete = async (constraintId: AdditionalConstraint["id"]) => {
    const constraintToDelete = constraints.find(({ id }) => id === constraintId);

    if (!constraintToDelete) {
      return;
    }

    const isConfirm = await deleteAction.showConfirm({ data: { name: constraintToDelete.name } });

    if (!isConfirm) {
      return;
    }

    try {
      setConstraints((prevConstraints) => prevConstraints.filter(({ id }) => id !== constraintId));

      await deleteAdditionalConstraints({
        studyId,
        areaId,
        storageId,
        constraintIds: [constraintId],
      });
    } catch (err) {
      setConstraints((prevConstraints) => [...prevConstraints, constraintToDelete]);

      enqueueErrorSnackbar(
        t("study.modelization.storages.additionalConstraints.delete.error", {
          name: constraintToDelete.name,
        }),
        toError(err),
      );
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (isRejected) {
    return <EmptyView title={error?.toString()} />;
  }

  const constraintsList = (
    <List sx={{ overflow: "auto" }}>
      {filteredAndSortedConstraints.map((constraint) => (
        <ListItem key={constraint.id} disablePadding dense>
          <ListItemButton
            selected={selectedConstraintId === constraint.id}
            onClick={() => setSelectedConstraintId(constraint.id)}
          >
            <Tooltip title={constraint.name}>
              <ListItemText
                primary={constraint.name}
                slotProps={{
                  primary: {
                    sx: {
                      textWrap: "nowrap",
                      textOverflow: "ellipsis",
                      overflow: "hidden",
                    },
                  },
                }}
              />
            </Tooltip>
          </ListItemButton>
        </ListItem>
      ))}
    </List>
  );

  return (
    <>
      <SplitView id="storage-additionalConstraints" sizes={[15, 85]}>
        {/* Left panel - Constraints list */}
        <Box>
          {isLoading ? (
            <SimpleLoader />
          ) : (
            <PropertiesView
              onSearchFilterChange={setSearchValue}
              onAdd={() => setAddDialogOpen(true)}
              mainContent={constraintsList}
            />
          )}
        </Box>

        {/* Right panel - Constraint form */}
        <ViewWrapper elevation={2}>
          {selectedConstraintId ? (
            <ConstraintForm
              studyId={studyId}
              areaId={areaId}
              storageId={storageId}
              constraintId={selectedConstraintId}
              onDelete={handleDelete}
            />
          ) : (
            <EmptyView />
          )}
        </ViewWrapper>
      </SplitView>
      <AddConstraintDialog
        open={addDialogOpen}
        onClose={() => setAddDialogOpen(false)}
        onSave={handleAdd}
        studyId={studyId}
        areaId={areaId}
        storageId={storageId}
        existingNames={constraints.map((c) => c.name)}
      />
      <ConfirmationDialog
        open={deleteAction.isPending}
        onConfirm={deleteAction.yes}
        onCancel={deleteAction.no}
        alert="error"
        titleIcon={DeleteIcon}
      >
        {t("study.modelization.storages.additionalConstraints.delete.confirm", {
          name: deleteAction.data?.name,
        })}
      </ConfirmationDialog>
    </>
  );
}

export default AdditionalConstraints;
