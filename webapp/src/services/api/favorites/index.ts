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

import client from "../client";
import type {
  FavoriteDirectory,
  FavoriteDirectoryParams,
  FavoriteStudy,
  FavoriteStudyParams,
} from "./types";

const STUDIES_FAVORITES_URL = `/v1/favorites/studies`;
const DIRECTORIES_FAVORITES_URL = `/v1/favorites/directories`;

/**
 * GET /v1/favorites/studies - Gets the list of the user's favorite studies.
 *
 * @returns List of the user's favorite studies.
 */
export async function getFavoriteStudies() {
  const { data } = await client.get<FavoriteStudy[]>(STUDIES_FAVORITES_URL);
  return data;
}

/**
 * POST /v1/favorites/studies/{studyId} - Adds a study to the user's favorites.
 *
 * @param params - Parameters for creating a favorite study.
 * @param params.studyId - ID of the study to add to favorites.
 * @returns The created object representing the favorite study.
 */
export async function createFavoriteStudy({ studyId }: FavoriteStudyParams) {
  const { data } = await client.post<FavoriteStudy>(`${STUDIES_FAVORITES_URL}/${studyId}`);
  return data;
}

/**
 * DELETE /v1/favorites/studies/{studyId} - Deletes a study from the user's favorites.
 *
 * @param params - Parameters for deleting a favorite study.
 * @param params.studyId - ID of the study to delete from favorites.
 */
export async function deleteFavoriteStudy({ studyId }: FavoriteStudyParams) {
  await client.delete(`${STUDIES_FAVORITES_URL}/${studyId}`);
}

/**
 * GET /v1/favorites/directories - Gets the list of the user's favorite directories.
 *
 * @returns List of the user's favorite directories.
 */
export async function getFavoriteDirectories() {
  const { data } = await client.get<FavoriteDirectory[]>(DIRECTORIES_FAVORITES_URL);
  return data;
}

/**
 * POST /v1/favorites/directories/{directoryId} - Adds a directory to the user's favorites.
 *
 * @param params - Parameters for creating a favorite directory.
 * @param params.directoryId - ID of the directory to add to favorites.
 * @returns The created object representing the favorite directory.
 */
export async function createFavoriteDirectory({ directoryId }: FavoriteDirectoryParams) {
  const { data } = await client.post<FavoriteDirectory>(
    `${DIRECTORIES_FAVORITES_URL}/${directoryId}`,
  );
  return data;
}

/**
 * DELETE /v1/favorites/directories/{directoryId} - Deletes a directory from the user's favorites.
 *
 * @param params - Parameters for deleting a favorite directory.
 * @param params.directoryId - ID of the directory to delete from favorites.
 */
export async function deleteFavoriteDirectory({ directoryId }: FavoriteDirectoryParams) {
  await client.delete(`${DIRECTORIES_FAVORITES_URL}/${directoryId}`);
}
