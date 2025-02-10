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

/**
 * Triggers the download of a file with the given data and name.
 *
 * @param fileData - The data of the file to be downloaded.
 * @param fileName - The name of the file to be downloaded.
 */
export function downloadFile(fileData: BlobPart, fileName: string) {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob([fileData]));
  link.download = fileName;
  link.click();
  URL.revokeObjectURL(link.href);
}
