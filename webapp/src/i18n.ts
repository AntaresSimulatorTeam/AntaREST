/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import i18n from "i18next";
import Backend from "i18next-http-backend";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";

export const SUPPORTED_LANGUAGES = ["en", "fr"] as const;

i18n
  // Learn more: https://github.com/i18next/i18next-http-backend
  .use(Backend)
  // Learn more: https://github.com/i18next/i18next-browser-languageDetector
  .use(LanguageDetector)
  // Learn more: https://react.i18next.com/latest/i18next-instance
  .use(initReactI18next)
  // For all options read: https://www.i18next.com/overview/configuration-options
  .init({
    supportedLngs: SUPPORTED_LANGUAGES,
    fallbackLng: "en",
    load: "languageOnly",
    cleanCode: true,
    ns: ["main"], // TODO: Add more namespaces https://www.i18next.com/principles/namespaces
    defaultNS: "main",
    // i18next-http-backend
    backend: {
      loadPath: `${
        import.meta.env.BASE_URL
      }locales/{{lng}}/{{ns}}.json?id=${__BUILD_TIMESTAMP__}`,
    },
    // i18next-browser-languagedetector
    detection: {
      convertDetectedLanguage: (lng) => lng.split("-")[0], // Remove region code (e.g. en-US -> en)
    },
    // react-i18next
    react: {
      useSuspense: false,
    },
  });

export default i18n;
