/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { useState } from "react";
import { useTranslation } from "react-i18next";

import AddCircleOutlineOutlinedIcon from "@mui/icons-material/AddCircleOutlineOutlined";
import UploadOutlinedIcon from "@mui/icons-material/UploadOutlined";
import { Button } from "@mui/material";

import ImportDialog from "@/components/common/dialogs/ImportDialog";
import { createStudy } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";

import CreateStudyDialog from "./CreateStudyDialog";

function HeaderRight() {
  const [openCreateDialog, setOpenCreateDialog] = useState(false);
  const [openImportDialog, setOpenImportDialog] = useState(false);
  const [t] = useTranslation();
  const dispatch = useAppDispatch();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleImport = (
    file: File,
    onUploadProgress: (progress: number) => void,
  ) => {
    return dispatch(
      createStudy({
        file,
        onUploadProgress,
      }),
    ).unwrap();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Button
        variant="outlined"
        color="primary"
        startIcon={<UploadOutlinedIcon />}
        onClick={() => setOpenImportDialog(true)}
      >
        {t("global.import")}
      </Button>
      <Button
        sx={{ ml: 2 }}
        variant="contained"
        color="primary"
        startIcon={<AddCircleOutlineOutlinedIcon />}
        onClick={() => setOpenCreateDialog(true)}
      >
        {t("global.create")}
      </Button>
      {openCreateDialog && (
        <CreateStudyDialog
          open={openCreateDialog}
          onClose={() => setOpenCreateDialog(false)}
        />
      )}
      {openImportDialog && (
        <ImportDialog
          open={openImportDialog}
          title={t("studies.importNewStudy")}
          dropzoneText={t("studies.importHint")}
          onCancel={() => setOpenImportDialog(false)}
          onImport={handleImport}
        />
      )}
    </>
  );
}

export default HeaderRight;
