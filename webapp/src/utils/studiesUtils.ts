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

import moment from "moment";
import * as R from "ramda";
import * as RA from "ramda-adjunct";
import type { StudiesSortConf, StudyFilters } from "../redux/ducks/studies";
import { StudyType, type StudyMetadata } from "../types/types";
import { isSearchMatching } from "./stringUtils";
import { validateString } from "./validation/string";

////////////////////////////////////////////////////////////////
// Sort
////////////////////////////////////////////////////////////////

export function sortStudies(sortConf: StudiesSortConf, studies: StudyMetadata[]): StudyMetadata[] {
  return R.sort((studyA, studyB) => {
    const first = sortConf.order === "ascend" ? studyA : studyB;
    const second = sortConf.order === "ascend" ? studyB : studyA;
    if (sortConf.property === "name") {
      return first.name.localeCompare(second.name);
    }
    return moment(first.modificationDate).isAfter(moment(second.modificationDate)) ? 1 : -1;
  }, studies);
}

////////////////////////////////////////////////////////////////
// Predicates
////////////////////////////////////////////////////////////////

const folderPredicate = R.curry((filters: StudyFilters, study: StudyMetadata) => {
  const { activeTree, managed, external } = filters;

  if (activeTree === "managed") {
    // Only show managed studies
    if (!study.managed) {
      return false;
    }

    // If directoryId is null, show studies with no directoryId (home/default)
    // Otherwise, show only studies in the selected directory
    return managed.directoryId === null
      ? study.directoryId === null
      : study.directoryId === managed.directoryId;
  }

  // activeTree === "external"
  // Only show external studies
  if (study.managed) {
    return false;
  }

  const workspacePath = `/${study.workspace}`;
  const studyPath = study.folder
    ? `${workspacePath}/${R.dropLast(1, study.folder.split("/")).join("/")}`
    : workspacePath;

  return external.path === ""
    ? true // home: show all external studies
    : external.strictPath
      ? studyPath === external.path
      : `${studyPath}/`.startsWith(`${external.path}/`);
});

const searchPredicate = R.curry((search: StudyFilters["search"], study: StudyMetadata) => {
  return search ? isSearchMatching(search, [study.name, study.id]) : true;
});

const tagsPredicate = R.curry((tags: StudyFilters["tags"], study: StudyMetadata) => {
  if (tags.length === 0) {
    return true;
  }
  if (!study.tags || study.tags.length === 0) {
    return false;
  }
  const upperCaseTags = tags.map((tag) => tag.toUpperCase());
  const upperCaseStudyTags = study.tags.map((tag) => tag.toUpperCase());
  return R.intersection(upperCaseStudyTags, upperCaseTags).length > 0;
});

const versionsPredicate = R.curry((versions: StudyFilters["versions"], study: StudyMetadata) => {
  return versions.length === 0 || versions.includes(study.version);
});

const usersPredicate = R.curry((users: StudyFilters["users"], study: StudyMetadata) => {
  if (users.length === 0) {
    return true;
  }
  return RA.isNumber(study.owner.id) && users.includes(study.owner.id);
});

const groupsPredicate = R.curry((groups: StudyFilters["groups"], study: StudyMetadata) => {
  return groups.length === 0 || R.intersection(study.groups.map(R.prop("id")), groups).length > 0;
});

const managementPredicate = R.curry(
  (management: StudyFilters["management"], study: StudyMetadata) => {
    if (management === "managed") {
      return study.managed === true;
    }
    if (management === "unmanaged") {
      return study.managed === false;
    }
    return true;
  },
);

const archivePredicate = R.curry((archive: StudyFilters["archive"], study: StudyMetadata) => {
  if (archive === "archived") {
    return study.archived === true;
  }
  if (archive === "unarchived") {
    return study.archived === false;
  }
  return true;
});

const typePredicate = R.curry((scope: StudyFilters["type"], study: StudyMetadata) => {
  if (scope === "references") {
    return study.type === StudyType.RAW;
  }
  if (scope === "variants") {
    return study.type === StudyType.VARIANT;
  }
  return true;
});

////////////////////////////////////////////////////////////////
// Filter
////////////////////////////////////////////////////////////////

export function filterStudies(filters: StudyFilters, studies: StudyMetadata[]): StudyMetadata[] {
  const predicates = [
    folderPredicate(filters),
    searchPredicate(filters.search),
    tagsPredicate(filters.tags),
    versionsPredicate(filters.versions),
    usersPredicate(filters.users),
    groupsPredicate(filters.groups),
    managementPredicate(filters.management),
    archivePredicate(filters.archive),
    typePredicate(filters.type),
  ] as RA.Pred[];
  return R.filter(R.allPass(predicates), studies);
}

////////////////////////////////////////////////////////////////
// Validation
////////////////////////////////////////////////////////////////

export const validateStudyName = validateString({
  specialChars: { chars: "=/", mode: "deny" },
});
