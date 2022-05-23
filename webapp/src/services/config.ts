import debug from "debug";
import axios from "axios";
import moment from "moment";
import { initAxiosClient } from "./api/client";
import { initRawAxiosClient } from "./api/auth";
import { APIVersion, getVersion } from "./api/misc";

const info = debug("antares:config:info");
const warn = debug("antares:config:warn");
const isDevEnv = process.env.NODE_ENV === "development";

moment.locale("fr", {
  months:
    "janvier_février_mars_avril_mai_juin_juillet_août_septembre_octobre_novembre_décembre".split(
      "_"
    ),
  monthsShort:
    "janv._févr._mars_avr._mai_juin_juil._août_sept._oct._nov._déc.".split("_"),
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
  ordinal(number) {
    return number + (number === 1 ? "er" : "e");
  },
  meridiemParse: /PD|MD/,
  isPM(input) {
    return input.charAt(0) === "M";
  },
  // In case the meridiem units are not separated around 12, then implement
  // this function (look at locale/id.js for an example).
  // meridiemHour : function (hour, meridiem) {
  //     return /* 0-23 hour, given meridiem token and hour 1-12 */ ;
  // },
  meridiem(hours, minutes, isLower) {
    return hours < 12 ? "PD" : "MD";
  },
  week: {
    dow: 1, // Monday is the first day of the week.
    doy: 4, // Used to determine first week of the year.
  },
});

export interface Config {
  baseUrl: string;
  applicationHome: string;
  restEndpoint: string;
  wsUrl: string;
  wsEndpoint: string;
  hidden: boolean;
  version: APIVersion;
  maintenanceMode: boolean;
  downloadHostUrl?: string;
}

let config = {
  applicationHome: "",
  restEndpoint: "",
  wsEndpoint: "/ws",
  hidden: false,
  version: {
    version: "unknown",
    gitcommit: "unknown",
  },
  maintenanceMode: false,
  ...(isDevEnv
    ? {
        baseUrl: "http://localhost:3000",
        wsUrl: "ws://localhost:8080",
        downloadHostUrl: "http://localhost:8080",
      }
    : {
        baseUrl: window.location.origin,
        wsUrl: `ws${window.location.protocol === "https:" ? "s" : ""}://${
          window.location.host
        }`,
      }),
} as Config;

export const getConfig = (): Readonly<Config> => config;

export const initConfig = async (
  callback: (appConfig: Config) => void
): Promise<void> => {
  try {
    const res = await axios.get("/config.json", { baseURL: "/" });
    config = {
      ...config,
      ...res.data,
    };
  } catch (e) {
    warn("Failed to retrieve site config. Will use default env configuration.");
  }

  initAxiosClient(config);
  initRawAxiosClient(config);

  try {
    const res = await getVersion();
    config = {
      ...config,
      version: res,
    };
  } catch (e) {
    warn("Failed to retrieve API Version");
  }

  info("config is", config);
  // to let the initAxiosClient complete
  setTimeout(() => callback(config), 50);
};
