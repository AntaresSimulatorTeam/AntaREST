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

import { Checkbox, type CheckboxProps, Tooltip } from "@mui/material";
import StarIcon from "@mui/icons-material/Star";
import StarBorderIcon from "@mui/icons-material/StarBorder";
import { toggleFavorite } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import { useTranslation } from "react-i18next";
import type { StudyMetadata } from "@/types/types";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { isStudyFavorite } from "@/redux/selectors";

export interface FavoriteStudyToggleProps {
  studyId: StudyMetadata["id"];
  size?: CheckboxProps["size"];
}

function FavoriteStudyToggle({ studyId, size }: FavoriteStudyToggleProps) {
  const isFavorite = useAppSelector((state) => isStudyFavorite(state, studyId));
  const dispatch = useAppDispatch();
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = () => {
    dispatch(toggleFavorite(studyId));
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
