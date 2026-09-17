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

import type {
  FavoriteDirectory,
  FavoriteExternalDirectory,
  FavoriteStudy,
} from "@/services/api/favorites/types";
import type { FavoriteButtonProps } from "./FavoriteButton";
import FavoriteDirectoryToggle from "./FavoriteDirectoryToggle";
import FavoriteExternalDirectoryToggle from "./FavoriteExternalDirectoryToggle";
import FavoriteStudyToggle from "./FavoriteStudyToggle";

interface Props {
  favorite: FavoriteStudy | FavoriteDirectory | FavoriteExternalDirectory;
  edge?: FavoriteButtonProps["edge"];
  tooltipPlacement?: FavoriteButtonProps["tooltipPlacement"];
}

function FavoriteToggle({ favorite, ...rest }: Props) {
  if ("directoryId" in favorite) {
    return <FavoriteDirectoryToggle directoryId={favorite.directoryId} {...rest} />;
  }

  if ("workspace" in favorite) {
    return (
      <FavoriteExternalDirectoryToggle
        workspace={favorite.workspace}
        path={favorite.path}
        {...rest}
      />
    );
  }

  return <FavoriteStudyToggle studyId={favorite.studyId} {...rest} />;
}

export default FavoriteToggle;
