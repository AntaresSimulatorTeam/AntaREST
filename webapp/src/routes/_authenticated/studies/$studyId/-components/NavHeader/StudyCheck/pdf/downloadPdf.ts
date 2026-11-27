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

import type { TDocumentDefinitions } from "pdfmake/interfaces";

type PdfMake = typeof import("pdfmake/build/pdfmake");

function unwrapCommonJsModule<T extends object>(module: T | { default: T }): T {
  return "default" in module ? module.default : module;
}

/**
 * Generates a PDF in the browser and has it downloaded.
 *
 * `pdfmake` and its fonts (about 2 MB) are only loaded when this function is called: they stay out
 * of the pages of the application.
 *
 * @param definition - Definition of the document, for `pdfmake`.
 * @param fileName - Name of the downloaded file.
 */
export async function downloadPdf(
  definition: TDocumentDefinitions,
  fileName: string,
): Promise<void> {
  const [pdfMakeModule, fontsModule] = await Promise.all([
    import("pdfmake/build/pdfmake"),
    import("pdfmake/build/vfs_fonts"),
  ]);
  const pdfMake = unwrapCommonJsModule<PdfMake>(pdfMakeModule);

  pdfMake.addVirtualFileSystem(unwrapCommonJsModule(fontsModule));
  await pdfMake.createPdf(definition).download(fileName);
}
