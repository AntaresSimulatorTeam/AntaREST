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

import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { Box, Button } from "@mui/material";
import type { StudyMetadata } from "@/types/types";
import { CommandEnum } from "@/components/App/Singlestudy/Commands/Edition/commandTypes";
import BasicDialog from "@/components/common/dialogs/BasicDialog";
import DataPropsView from "@/components/App/Data/DataPropsView";
import FileTable from "@/components/common/FileTable";
import SplitView from "@/components/common/SplitView";
import { getMatrixList } from "@/services/api/matrix";
import { appendCommands } from "@/services/api/variant";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import MatrixContent from "./components/MatrixContent";
import { toError } from "@/utils/fnUtils";
import SimpleLoader from "@/components/common/loaders/SimpleLoader";

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
        <SplitView id="matrix-assign" sizes={[20, 80]}>
          <DataPropsView
            dataset={matrices || []}
            selectedItem={selectedItem}
            setSelectedItem={setSelectedItem}
          />
          <Box sx={{ width: 1, height: 1, px: 2 }}>
            {selectedItem &&
              (matrix ? (
                <MatrixContent matrix={matrix} onBack={() => setMatrixId(undefined)} />
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
