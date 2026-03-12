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

import type { StudyMetadata } from "@/types/types";
import StarIcon from "@mui/icons-material/Star";
import StarBorderIcon from "@mui/icons-material/StarBorder";
import { Checkbox, type CheckboxProps, Tooltip } from "@mui/material";
import { useTranslation } from "react-i18next";

interface Props {
  studyId: StudyMetadata["id"];
  size?: CheckboxProps["size"];
}

function FavoriteStudyToggle({ studyId, size }: Props) {
  const isFavorite = false;
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = () => {
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Tooltip title={isFavorite ? t("studies.removeFavorite") : t("studies.addFavorite")}>
      <Checkbox
        size={size}
        checked={isFavorite}
        icon={<StarBorderIcon />}
        checkedIcon={<StarIcon />}
        onClick={(event) => event.stopPropagation()}
        onChange={handleChange}
      />
    </Tooltip>
  );
}

export default FavoriteStudyToggle;
