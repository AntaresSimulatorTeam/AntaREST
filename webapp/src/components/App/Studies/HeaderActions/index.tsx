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

import { Button, Divider } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import AddCircleOutlineOutlinedIcon from "@mui/icons-material/AddCircleOutlineOutlined";
import UploadOutlinedIcon from "@mui/icons-material/UploadOutlined";
import { createStudy, updateStudyFilters } from "@/redux/ducks/studies";
import UploadDialog, { type UploadDialogProps } from "../../../common/dialogs/UploadDialog";
import CreateStudyDialog from "../CreateStudyDialog";
import useAppDispatch from "../../../../redux/hooks/useAppDispatch";
import SearchFE from "@/components/common/fieldEditors/SearchFE";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudyFilters } from "@/redux/selectors";
import FilterTags from "@/components/App/Studies/HeaderActions/FliterTags";
import FilterAltIcon from "@mui/icons-material/FilterAlt";

interface Props {
  onOpenFilterClick: VoidFunction;
}

function HeaderActions({ onOpenFilterClick }: Props) {
  const [dialog, setDialog] = useState<null | "create" | "upload">();
  const searchValue = useAppSelector((state) => getStudyFilters(state).inputValue);
  const dispatch = useAppDispatch();
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const setSearchValue = (newValue = "") => {
    dispatch(updateStudyFilters({ inputValue: newValue }));
  };

  const closeDialog = () => setDialog(null);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleImport: UploadDialogProps["onImport"] = (file, onUploadProgress) => {
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
      <FilterTags />
      <Button
        color="secondary"
        variant="outlined"
        onClick={onOpenFilterClick}
        startIcon={<FilterAltIcon />}
      >
        {t("global.filters")}
      </Button>
      <SearchFE
        size="extra-small"
        value={searchValue}
        onSearchValueChange={setSearchValue}
        onClear={setSearchValue}
        sx={{ maxWidth: 200 }}
      />
      <Divider flexItem orientation="vertical" variant="middle" />
      <Button
        variant="outlined"
        startIcon={<UploadOutlinedIcon />}
        onClick={() => setDialog("upload")}
      >
        {t("global.import")}
      </Button>
      <Button
        variant="contained"
        startIcon={<AddCircleOutlineOutlinedIcon />}
        onClick={() => setDialog("create")}
      >
        {t("global.create")}
      </Button>
      {dialog === "create" && <CreateStudyDialog open onClose={closeDialog} />}
      {dialog === "upload" && (
        <UploadDialog
          open
          title={t("studies.importNewStudy")}
          dropzoneText={t("studies.importHint")}
          onCancel={closeDialog}
          onImport={handleImport}
        />
      )}
    </>
  );
}

export default HeaderActions;
