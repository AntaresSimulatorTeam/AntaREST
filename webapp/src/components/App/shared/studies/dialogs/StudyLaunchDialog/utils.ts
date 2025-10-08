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

import {
  getLaunchersConfig,
  getLauncherVersions,
  getStudyOutputs,
  type Launcher,
} from "@/services/api/study";
import { displayVersionName } from "@/services/utils";
import type { StudyMetadata } from "@/types/types";
import * as R from "ramda";

export const XPRESS_OPTION = "xpress" as const;

export const NULL_LAUNCHER: Readonly<Launcher> = {
  id: "",
  name: "",
  nbCores: { min: 0, max: 0, default: 0 },
  timeLimit: { min: 0, max: 0, default: 0 },
};

export const getDefaultValues = async (studyIds: Array<StudyMetadata["id"]>) => {
  const config = await getLaunchersConfig();
  const versions = await getLauncherVersions();

  const launchersById = R.indexBy(R.prop("id"), config.launchers);
  const launcherOptions = config.launchers.map(({ id, name }) => ({ value: id, label: name }));
  const launcher = launchersById[config.defaultLauncher];

  const versionOptions = versions.map((version) => ({
    value: version,
    label: displayVersionName(version),
  }));

  const isSingleStudy = studyIds.length === 1;
  const studyOutputs = isSingleStudy ? await getStudyOutputs(studyIds[0]) : [];
  const outputOptions = studyOutputs.map(({ name }) => name);

  return {
    name: "",
    version: "",
    otherOptions: "",
    xpress: false,
    autoUnzip: true,
    xpansion: false,
    sensitivityMode: false,
    output: "",
    launcher: launcher.id,
    nbCores: launcher.nbCores.default,
    timeLimit: launcher.timeLimit.default,
    // Replace by implementing metadata in `Form` if it's not implemented yet by react-hook-form
    // https://github.com/react-hook-form/react-hook-form/issues/13036
    _data: {
      launchersById,
      launcherOptions,
      versionOptions,
      outputOptions,
      isSingleStudy,
    },
  };
};

export type FormValues = Awaited<ReturnType<typeof getDefaultValues>>;

export const otherOptionsToArray = (otherOptions: string): string[] => {
  return otherOptions.trim() === "" ? [] : otherOptions.split(/\s+/);
};

export const isXpressAvailableForVersion = (version: FormValues["version"]) => {
  return Number(version) >= 830;
};
