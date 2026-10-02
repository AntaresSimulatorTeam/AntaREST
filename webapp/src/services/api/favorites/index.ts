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

import z from "zod";
import client from "../client";
import {
  favoriteDirectorySchema,
  favoriteExternalDirectorySchema,
  favoriteStudySchema,
} from "./schemas";
import type {
  FavoriteDirectory,
  FavoriteDirectoryParams,
  FavoriteExternalDirectory,
  FavoriteStudy,
  FavoriteStudyParams,
} from "./types";

const STUDIES_FAVORITES_URL = `/v1/favorites/studies`;
const DIRECTORIES_FAVORITES_URL = `/v1/favorites/directories`;
const EXTERNAL_DIRECTORIES_FAVORITES_URL = `/v1/favorites/external-directories`;

/**
 * GET /v1/favorites/studies - Gets the list of the user's favorite studies.
 *
 * @returns List of the user's favorite studies.
 */
export async function getFavoriteStudies(): Promise<FavoriteStudy[]> {
  const { data } = await client.get(STUDIES_FAVORITES_URL);
  return z.array(favoriteStudySchema).parse(data);
}

/**
 * POST /v1/favorites/studies/{studyId} - Adds a study to the user's favorites.
 *
 * @param params - Parameters for creating a favorite study.
 * @param params.studyId - ID of the study to add to favorites.
 * @returns The created object representing the favorite study.
 */
export async function createFavoriteStudy({
  studyId,
}: FavoriteStudyParams): Promise<FavoriteStudy> {
  const { data } = await client.post(`${STUDIES_FAVORITES_URL}/${studyId}`);
  return favoriteStudySchema.parse(data);
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
export async function getFavoriteDirectories(): Promise<FavoriteDirectory[]> {
  const { data } = await client.get(DIRECTORIES_FAVORITES_URL);
  return z.array(favoriteDirectorySchema).parse(data);
}

/**
 * POST /v1/favorites/directories/{directoryId} - Adds a directory to the user's favorites.
 *
 * @param params - Parameters for creating a favorite directory.
 * @param params.directoryId - ID of the directory to add to favorites.
 * @returns The created object representing the favorite directory.
 */
export async function createFavoriteDirectory({
  directoryId,
}: FavoriteDirectoryParams): Promise<FavoriteDirectory> {
  const { data } = await client.post(`${DIRECTORIES_FAVORITES_URL}/${directoryId}`);
  return favoriteDirectorySchema.parse(data);
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

/**
 * GET /v1/favorites/external-directories - Gets the list of the user's favorite external directories.
 *
 * @returns List of the user's favorite external directories.
 */
export async function getFavoriteExternalDirectories(): Promise<FavoriteExternalDirectory[]> {
  const { data } = await client.get(EXTERNAL_DIRECTORIES_FAVORITES_URL);
  return z.array(favoriteExternalDirectorySchema).parse(data);
}

/**
 * POST /v1/favorites/external-directories - Adds an external directory to the user's favorites.
 *
 * @param params - Parameters for creating a favorite external directory.
 * @param params.workspace - Workspace of the external directory to add to favorites.
 * @param params.path - Path of the external directory to add to favorites.
 * @returns The created object representing the favorite external directory.
 */
export async function createFavoriteExternalDirectory(
  params: FavoriteExternalDirectory,
): Promise<FavoriteExternalDirectory> {
  const { data } = await client.post(EXTERNAL_DIRECTORIES_FAVORITES_URL, null, { params });
  return favoriteExternalDirectorySchema.parse(data);
}

/**
 * DELETE /v1/favorites/external-directories - Deletes an external directory from the user's favorites.
 *
 * @param params - Parameters for deleting a favorite external directory.
 * @param params.workspace - Workspace of the external directory to delete from favorites.
 * @param params.path - Path of the external directory to delete from favorites.
 */
export async function deleteFavoriteExternalDirectory(params: FavoriteExternalDirectory) {
  await client.delete(EXTERNAL_DIRECTORIES_FAVORITES_URL, { params });
}
