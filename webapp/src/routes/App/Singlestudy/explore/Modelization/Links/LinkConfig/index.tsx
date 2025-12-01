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

import { Chip, Divider } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router";
import type { LinkElement, StudyMetadata } from "../../../../../../../types/types";
import LinkForm from "./LinkForm";
import LinkMatrices from "./LinkMatrices";

interface Props {
  link: LinkElement;
}

function LinkConfig({ link }: Props) {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { t } = useTranslation();
  const studyVersion = Number(study.version);
  const isOldStudy = studyVersion < 820;

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <LinkForm link={link} study={study} isOldStudy={isOldStudy} />
      <Divider sx={{ my: 2 }} variant="middle">
        <Chip label={isOldStudy ? t("global.matrice") : t("global.matrices")} size="small" />
      </Divider>
      <LinkMatrices study={study} area1={link.area1} area2={link.area2} isOldStudy={isOldStudy} />
    </>
  );
}

export default LinkConfig;
