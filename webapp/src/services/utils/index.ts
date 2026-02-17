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

import i18n from "@/i18n";
import { toSemanticVersion } from "@/utils/versionUtils";
import type { TFunction } from "i18next";
import moment from "moment";
import * as R from "ramda";
import {
  type GenericInfo,
  type JWTGroup,
  RoleType,
  type StudyMetadata,
  type StudyMetadataDTO,
  type UserInfo,
  type VariantTree,
  type VariantTreeDTO,
} from "../../types/types";

export const convertStudyDtoToMetadata = (
  sid: string,
  metadata: StudyMetadataDTO,
): StudyMetadata => {
  return {
    id: sid,
    name: metadata.name,
    creationDate: metadata.created,
    modificationDate: metadata.updated,
    owner: metadata.owner,
    author: metadata.author,
    editor: metadata.editor,
    groups: metadata.groups,
    type: metadata.type,
    publicMode: metadata.public_mode,
    version: toSemanticVersion(metadata.version),
    workspace: metadata.workspace,
    managed: metadata.managed,
    archived: metadata.archived,
    folder: metadata.folder,
    horizon: metadata.horizon,
    tags: metadata.tags,
    parentId: metadata.parent_id,
    directoryId: metadata.directory_id,
  };
};

export const convertVariantTreeDTO = (variantTree: VariantTreeDTO): VariantTree => ({
  node: convertStudyDtoToMetadata(variantTree.node.id, variantTree.node),
  children: (variantTree.children || []).map((child: VariantTreeDTO) =>
    convertVariantTreeDTO(child),
  ),
});

export const isUserAdmin = (user?: UserInfo): boolean => {
  if (user) {
    const adminElm = user.groups.find(
      (elm: JWTGroup) => elm.id === "admin" && elm.role === RoleType.ADMIN,
    );
    return !!adminElm;
  }
  return false;
};

export const isUserExpired = (user: UserInfo): boolean => {
  return !user.expirationDate || moment.unix(user.expirationDate) < moment().add(5, "s");
};

export const isGroupAdmin = (user?: UserInfo): boolean => {
  if (user) {
    const adminElm = user.groups.find((elm: JWTGroup) => elm.role === RoleType.ADMIN);
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
  role: RoleType,
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
            (userGroupElm) => studyGroupElm.id === userGroupElm.id && userGroupElm.role >= role,
          ),
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
  moment.duration(moment(Date.now()).diff(moment(convertUTCToLocalTime(date))), "milliseconds");

export const exportText = (fileData: string, filename: string): void => {
  const blob = new Blob([fileData], { type: "application/txt" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.download = filename;
  link.href = url;
  link.click();
  link.remove();
};

export const isStringEmpty = (data: string): boolean => data.replace(/\s/g, "") === "";

export const buildModificationDate = (
  date: string,
  t: TFunction<"translation", undefined>,
  language = "en",
): string => {
  const duration = modificationDate(date);
  return duration.locale(language.substring(0, 2) === "fr" ? "fr" : "en").humanize();
};

export const countDescendants = (tree: VariantTree): number =>
  tree.children.length
    ? tree.children.reduce((sum, child) => sum + 1 + countDescendants(child), 0)
    : 0;

export const findNodeInTree = (studyId: string, tree: VariantTree): VariantTree | undefined => {
  if (studyId === tree.node.id) {
    return tree;
  }
  for (const child of tree.children) {
    const elm = findNodeInTree(studyId, child);
    if (elm !== undefined) {
      return elm;
    }
  }
  return undefined;
};

export const createListFromTree = ({ node, children }: VariantTree): GenericInfo[] => {
  const { id, name } = node;

  return children.reduce<GenericInfo[]>(
    (list, tree) => list.concat(createListFromTree(tree)),
    [{ id, name }],
  );
};

export const sortByProp = <K extends string, T extends Record<K, string>>(key: K, list: T[]) =>
  R.sortBy(R.compose(R.toLower, R.prop(key)), list);

export const sortByName = <T extends { name: string }>(list: T[]) => sortByProp("name", list);

export const getNames = <T extends { name: string }>(list: T[]) => list.map((c) => c.name);

/**
 * Converts a name string to a valid ID string.
 * Replacing any characters that are not alphanumeric or -_,()& with a space,
 * trimming the resulting string, and converting it to lowercase.
 *
 * @param name - The name string to convert to an ID.
 * @returns The resulting ID string.
 */
export const nameToId = (name: string): string => {
  return name
    .replace(/[^a-zA-Z0-9_\-(),& ]+|\s+/g, " ")
    .trim()
    .toLowerCase();
};

export const removeEmptyFields = (
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: Record<string, any>,
  fieldsToCheck: string[],
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
): Record<string, any> => {
  const cleanData = { ...data };

  fieldsToCheck.forEach((fieldName) => {
    if (R.isEmpty(data[fieldName])) {
      delete cleanData[fieldName];
    }
  });

  return cleanData;
};

export default {};
