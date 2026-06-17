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

import FilterTags from "@/routes/_authenticated/studies/-components/HeaderActions/FilterTags";
import ImportStudyDialog from "@/routes/-shared/components/studies/dialogs/ImportStudyDialog";
import AddCircleOutlineOutlinedIcon from "@mui/icons-material/AddCircleOutlineOutlined";
import FilterAltIcon from "@mui/icons-material/FilterAlt";
import UploadOutlinedIcon from "@mui/icons-material/UploadOutlined";
import { Button, Divider } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import CreateStudyDialog from "../CreateStudyDialog";
import SearchStudies from "./SearchStudies";

interface Props {
  onOpenFilterClick: VoidFunction;
}

function HeaderActions({ onOpenFilterClick }: Props) {
  const [dialog, setDialog] = useState<null | "create" | "upload">();
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const closeDialog = () => setDialog(null);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <SearchStudies />
      <FilterTags />
      <Button
        color="secondary"
        variant="outlined"
        onClick={onOpenFilterClick}
        startIcon={<FilterAltIcon />}
      >
        {t("global.filters")}
      </Button>
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
      {dialog === "upload" && <ImportStudyDialog open onClose={closeDialog} />}
    </>
  );
}

export default HeaderActions;
