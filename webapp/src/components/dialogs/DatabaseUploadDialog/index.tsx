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

import BasicDialog from "@/components/dialogs/BasicDialog";
import FileTable from "@/components/FileTable";
import SimpleLoader from "@/components/loaders/SimpleLoader";
import SplitView from "@/components/page/SplitView";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import DataPropsView from "@/routes/_authenticated/data/-components/DataPropsView";
import { CommandEnum } from "@/routes/_authenticated/studies/$studyId/-components/NavHeader/CommandsDrawer/EditionView/commandTypes";
import { getMatrixList } from "@/services/api/matrix";
import { appendCommands } from "@/services/api/variant";
import type { StudyMetadata } from "@/types/types";
import { toError } from "@/utils/fnUtils";
import { Box, Button } from "@mui/material";
import { useSnackbar } from "notistack";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import MatrixContent from "./components/MatrixContent";

interface DatabaseUploadDialogProps {
  studyId: StudyMetadata["id"];
  path: string;
  open: boolean;
  onClose: () => void;
}

function DatabaseUploadDialog({ studyId, path, open, onClose }: DatabaseUploadDialogProps) {
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [isUploading, setIsUploading] = useState(false);
  const [selectedItem, setSelectedItem] = useState("");
  const [matrixId, setMatrixId] = useState<string>();

  const { data: matrices } = usePromiseWithSnackbarError(getMatrixList, {
    errorMessage: t("data.error.matrixList"),
  });

  const selectedMatrix = useMemo(
    () => matrices?.find((item) => item.id === selectedItem)?.matrices || [],
    [matrices, selectedItem],
  );

  const matrix = useMemo(() => {
    if (!matrixId || !selectedMatrix) {
      return undefined;
    }

    const matrix = selectedMatrix.find((m) => m.id === matrixId);
    return matrix ? { id: matrix.id, name: matrix.name } : undefined;
  }, [matrixId, selectedMatrix]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleMatrixClick = (id: string) => {
    setMatrixId(id);
  };

  const handleUpload = async (matrixId: string) => {
    setIsUploading(true);

    try {
      await appendCommands(studyId, [
        {
          action: CommandEnum.REPLACE_MATRIX,
          args: { target: path, matrix: matrixId },
        },
      ]);

      enqueueSnackbar(t("data.success.matrixAssignation"), {
        variant: "success",
      });

      onClose();
    } catch (err) {
      enqueueErrorSnackbar(t("data.error.matrixAssignation"), toError(err));
    } finally {
      setIsUploading(false);
    }
  };

  const handleClose = (
    _event: Record<string, never>,
    reason: "backdropClick" | "escapeKeyDown",
  ) => {
    if (!isUploading) {
      onClose();
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <BasicDialog
      title={t("matrix.importNewMatrix")}
      open={open}
      onClose={handleClose}
      disableEscapeKeyDown={isUploading} // Prevent Escape key during upload
      actions={
        <Button onClick={onClose} disabled={isUploading}>
          {t("global.close")}
        </Button>
      }
      maxWidth="xl"
      fullWidth
      contentProps={{
        sx: { p: 1, height: "95vh", width: 1 },
      }}
    >
      {isUploading ? (
        <SimpleLoader />
      ) : (
        <SplitView splitId="matrix-assign">
          <DataPropsView
            dataset={matrices || []}
            selectedItem={selectedItem}
            setSelectedItem={setSelectedItem}
          />
          <Box sx={{ width: 1, height: 1, px: 2 }}>
            {selectedItem &&
              (matrix ? (
                <MatrixContent matrixInfo={matrix} onBack={() => setMatrixId(undefined)} />
              ) : (
                <FileTable
                  title=""
                  content={selectedMatrix}
                  onRead={handleMatrixClick}
                  onAssign={handleUpload}
                />
              ))}
          </Box>
        </SplitView>
      )}
    </BasicDialog>
  );
}

export default DatabaseUploadDialog;
