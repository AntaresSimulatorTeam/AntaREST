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

import i18n from "i18next";
import Backend from "i18next-http-backend";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";
import moment from "moment";

export const SUPPORTED_LANGUAGES = ["en", "fr"] as const;

// From https://momentjs.com/docs/#/i18n/changing-locale/
moment.locale("fr", {
  months:
    "janvier_février_mars_avril_mai_juin_juillet_août_septembre_octobre_novembre_décembre".split(
      "_",
    ),
  monthsShort: "janv._févr._mars_avr._mai_juin_juil._août_sept._oct._nov._déc.".split("_"),
  monthsParseExact: true,
  weekdays: "dimanche_lundi_mardi_mercredi_jeudi_vendredi_samedi".split("_"),
  weekdaysShort: "dim._lun._mar._mer._jeu._ven._sam.".split("_"),
  weekdaysMin: "Di_Lu_Ma_Me_Je_Ve_Sa".split("_"),
  weekdaysParseExact: true,
  longDateFormat: {
    LT: "HH:mm",
    LTS: "HH:mm:ss",
    L: "DD/MM/YYYY",
    LL: "D MMMM YYYY",
    LLL: "D MMMM YYYY HH:mm",
    LLLL: "dddd D MMMM YYYY HH:mm",
  },
  calendar: {
    sameDay: "[Aujourd’hui à] LT",
    nextDay: "[Demain à] LT",
    nextWeek: "dddd [à] LT",
    lastDay: "[Hier à] LT",
    lastWeek: "dddd [dernier à] LT",
    sameElse: "L",
  },
  relativeTime: {
    future: "dans %s",
    past: "il y a %s",
    s: "quelques secondes",
    m: "une minute",
    mm: "%d minutes",
    h: "une heure",
    hh: "%d heures",
    d: "un jour",
    dd: "%d jours",
    M: "un mois",
    MM: "%d mois",
    y: "un an",
    yy: "%d ans",
  },
  dayOfMonthOrdinalParse: /\d{1,2}(er|e)/,
  ordinal: function (number) {
    return number + (number === 1 ? "er" : "e");
  },
  meridiemParse: /PD|MD/,
  isPM: function (input) {
    return input.charAt(0) === "M";
  },
  // In case the meridiem units are not separated around 12, then implement
  // this function (look at locale/id.js for an example).
  // meridiemHour : function (hour, meridiem) {
  //     return /* 0-23 hour, given meridiem token and hour 1-12 */ ;
  // },
  meridiem: function (hours, minutes, isLower) {
    return hours < 12 ? "PD" : "MD";
  },
  week: {
    dow: 1, // Monday is the first day of the week.
    doy: 4, // Used to determine first week of the year.
  },
});

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
      loadPath: `${import.meta.env.BASE_URL}locales/{{lng}}/{{ns}}.json?id=${__BUILD_TIMESTAMP__}`,
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
