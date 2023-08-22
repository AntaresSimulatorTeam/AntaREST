import moment from "moment";
import debug from "debug";
import i18n, { TFunction } from "i18next";
import * as R from "ramda";
import {
  StudyMetadataDTO,
  StudyMetadata,
  JWTGroup,
  UserInfo,
  RoleType,
  VariantTreeDTO,
  VariantTree,
  GenericInfo,
} from "../../common/types";
import { getMaintenanceMode, getMessageInfo } from "../api/maintenance";
import { getConfig } from "../config";

const logInfo = debug("antares:utils");

export const convertStudyDtoToMetadata = (
  sid: string,
  metadata: StudyMetadataDTO
): StudyMetadata => ({
  id: sid,
  name: metadata.name,
  creationDate: metadata.created,
  modificationDate: metadata.updated,
  owner: metadata.owner,
  groups: metadata.groups,
  type: metadata.type,
  publicMode: metadata.public_mode,
  version: metadata.version.toString(),
  workspace: metadata.workspace,
  managed: metadata.managed,
  archived: metadata.archived,
  folder: metadata.folder,
  horizon: metadata.horizon,
  scenario: metadata.scenario,
  status: metadata.status,
  doc: metadata.doc,
  tags: metadata.tags,
});

export const convertVariantTreeDTO = (
  variantTree: VariantTreeDTO
): VariantTree => ({
  node: convertStudyDtoToMetadata(variantTree.node.id, variantTree.node),
  children: (variantTree.children || []).map((child: VariantTreeDTO) =>
    convertVariantTreeDTO(child)
  ),
});

export const isUserAdmin = (user?: UserInfo): boolean => {
  if (user) {
    const adminElm = user.groups.find(
      (elm: JWTGroup) => elm.id === "admin" && elm.role === RoleType.ADMIN
    );
    return !!adminElm;
  }
  return false;
};

export const isUserExpired = (user: UserInfo): boolean => {
  return (
    !user.expirationDate ||
    moment.unix(user.expirationDate) < moment().add(5, "s")
  );
};

export const isGroupAdmin = (user?: UserInfo): boolean => {
  if (user) {
    const adminElm = user.groups.find(
      (elm: JWTGroup) => elm.role === RoleType.ADMIN
    );
    return !!adminElm;
  }
  return false;
};

export const roleToString = (role: RoleType): string => {
  switch (role) {
    case RoleType.ADMIN:
      return i18n.t("settings.adminRole");
    case RoleType.RUNNER:
      return i18n.t("settings.runnerRole");
    case RoleType.WRITER:
      return i18n.t("settings.writerRole");
    case RoleType.READER:
      return i18n.t("settings.readerRole");
    default:
      return "";
  }
};

export const hasAuthorization = (
  user: UserInfo | undefined,
  study: StudyMetadata,
  role: RoleType
): boolean => {
  if (user) {
    // User is super admin
    if (isUserAdmin(user)) {
      return true;
    }

    if (study) {
      // User is owner of this study
      if (study.owner.id && study.owner.id === user.id) {
        return true;
      }
      // User is admin of 1 of study groups
      return (
        study.groups.findIndex((studyGroupElm) =>
          user.groups.find(
            (userGroupElm) =>
              studyGroupElm.id === userGroupElm.id && userGroupElm.role >= role
          )
        ) >= 0
      );
    }
  }
  return false;
};

export const getStudyExtendedName = (study: StudyMetadata): string => {
  if (study.folder) {
    return `${study.name} (${study.folder})`;
  }
  return study.name;
};

export const convertUTCToLocalTime = (date: string): string =>
  moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss");

export const modificationDate = (date: string): moment.Duration =>
  moment.duration(
    moment(Date.now()).diff(moment(convertUTCToLocalTime(date))),
    "milliseconds"
  );

export const exportText = (fileData: string, filename: string): void => {
  const blob = new Blob([fileData], { type: "application/txt" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.download = filename;
  link.href = url;
  link.click();
  link.remove();
};

/**
 * Gets the appropriate version name to display.
 * The patch version is not displayed because it is not relevant.
 * Its value is always 0 from the server.
 *
 * Ex: '820' -> '8.2'
 *
 * @param v Version in format '[major][minor]0' (ex: '820').
 * @returns Version in format '[major].[minor]' (ex: '8.2').
 */
export const displayVersionName = (v: string): string => `${v[0]}.${v[1]}`;

export const convertVersions = (versions: Array<string>): Array<GenericInfo> =>
  versions.map((version) => ({
    id: version,
    name: displayVersionName(version),
  }));

export const getMaintenanceStatus = async (): Promise<boolean> => {
  const { maintenanceMode } = getConfig();
  try {
    const tmpMaintenance = await getMaintenanceMode();
    return tmpMaintenance;
  } catch (e) {
    logInfo("Failed to retrieve maintenance status", e);
  }
  return maintenanceMode;
};

export const getInitMessageInfo = async (): Promise<string> => {
  try {
    const tmpMessage = await getMessageInfo();
    return tmpMessage;
  } catch (e) {
    logInfo("Failed to retrieve message info", e);
  }
  return "";
};

export const isStringEmpty = (data: string): boolean =>
  data.replace(/\s/g, "") === "";

export const buildModificationDate = (
  date: string,
  t: TFunction<"translation", undefined>,
  language = "en"
): string => {
  const duration = modificationDate(date);
  return duration
    .locale(language.substring(0, 2) === "fr" ? "fr" : "en")
    .humanize();
};

export const countAllChildrens = (tree: VariantTree): number => {
  if (tree.children.length > 0) {
    return tree.children
      .map((elm) => 1 + countAllChildrens(elm))
      .reduce((acc, curr) => acc + curr);
  }
  return 0;
};

export const findNodeInTree = (
  studyId: string,
  tree: VariantTree
): VariantTree | undefined => {
  if (studyId === tree.node.id) {
    return tree;
  }
  for (let i = 0; i < tree.children.length; i += 1) {
    const elm = findNodeInTree(studyId, tree.children[i]);
    if (elm !== undefined) {
      return elm;
    }
  }
  return undefined;
};

export const createListFromTree = (tree: VariantTree): Array<GenericInfo> => {
  const { node, children } = tree;
  const { id, name } = node;
  let res: Array<GenericInfo> = [{ id, name }];
  children.forEach((elm) => {
    res = res.concat(createListFromTree(elm));
  });
  return res;
};

export const sortByProp = <T extends object>(
  getProp: (obj: T) => string,
  list: T[]
): T[] => {
  return R.sortBy(R.compose(R.toLower, getProp), list);
};

export const sortByName = <T extends { name: string }>(list: T[]): T[] => {
  return sortByProp((v) => v.name, list);
};

// This should work better
export const transformNameToId = (name: string): string => {
  let duppl = false;
  let id = "";

  for (
    let char, index = 0, str = name, { length } = str;
    index < length;
    index += 1
  ) {
    char = str[index];

    if (
      (char >= "a" && char <= "z") ||
      (char >= "A" && char <= "Z") ||
      (char >= "0" && char <= "9") ||
      char === "_" ||
      char === "-" ||
      char === "(" ||
      char === ")" ||
      char === "," ||
      char === "&" ||
      char === " "
    ) {
      id += char;
      duppl = false;
    } else if (!duppl) {
      id += " ";
      duppl = true;
    }
  }

  const idTrimmed = id.trim();

  return idTrimmed.toLowerCase();
};

export const removeEmptyFields = (
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: { [key: string]: any },
  fieldsToCheck: Array<string>
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
): { [key: string]: any } => {
  const cleanData = { ...data };

  fieldsToCheck.forEach((fieldName) => {
    if (R.isEmpty(data[fieldName])) {
      delete cleanData[fieldName];
    }
  });

  return cleanData;
};

export default {};
