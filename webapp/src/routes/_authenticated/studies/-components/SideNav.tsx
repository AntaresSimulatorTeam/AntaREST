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

import ListCollapse from "@/components/ListCollapse";
import StudyTree from "@/routes/_authenticated/studies/-components/StudyTree";
import AccountTreeIcon from "@mui/icons-material/AccountTree";
import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";

function SideNav() {
  const { t } = useTranslation();

  return (
    <Box sx={{ overflow: "auto" }}>
      <ListCollapse title={t("studies.exploration")} titleIcon={<AccountTreeIcon />}>
        <StudyTree />
      </ListCollapse>
    </Box>
  );
}

export default SideNav;
