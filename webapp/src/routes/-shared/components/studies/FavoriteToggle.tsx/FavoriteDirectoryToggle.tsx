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

import { directoryQueries } from "@/queries/directories/queries";
import type { Directory } from "@/services/api/directories/types";
import type { FavoriteDirectory } from "@/services/api/favorites/types";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useCallback } from "react";
import FavoriteButton, { type FavoriteButtonProps } from "./FavoriteButton";

interface Props {
  directoryId: Directory["id"];
  edge?: FavoriteButtonProps["edge"];
  tooltipPlacement?: FavoriteButtonProps["tooltipPlacement"];
}

function FavoriteDirectoryToggle({ directoryId, edge, tooltipPlacement }: Props) {
  const isFavoriteDirectory = useCallback(
    (favorites: FavoriteDirectory[]) => favorites.some((fav) => fav.directoryId === directoryId),
    [directoryId],
  );

  const { data: isFavorite } = useSuspenseQuery({
    ...directoryQueries.favorites(),
    select: isFavoriteDirectory,
  });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleClick = () => {
    //
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FavoriteButton
      isFavorite={isFavorite}
      onClick={handleClick}
      edge={edge}
      tooltipPlacement={tooltipPlacement}
    />
  );
}

export default FavoriteDirectoryToggle;
