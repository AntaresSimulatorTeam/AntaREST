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

import { getStudiesById } from "@/redux/selectors";
import store from "@/redux/store";
import { getLauncherVersions } from "@/services/api/launcher/index";
import { getSolverPresets } from "@/services/api/launcher/solverPresets";
import { getLaunchersConfig, getStudyOutputs, type Launcher } from "@/services/api/study";
import { displayVersionName } from "@/services/utils";
import type { StudyMetadata } from "@/types/types";
import * as R from "ramda";

export const XPRESS_OPTION = "xpress" as const;

export const getDefaultValues = async (studyIds: Array<StudyMetadata["id"]>) => {
  const { launchers: _launchers, defaultLauncher: defaultLauncherId } = await getLaunchersConfig();

  // TODO: Remove when API will provide versions with launchers
  const launchers = await Promise.all(
    _launchers.map(async (launcher) => {
      const versions = await getLauncherVersions({ launcherId: launcher.id });
      return { ...launcher, versions };
    }),
  );

  const launchersById = R.indexBy(R.prop("id"), launchers);
  const defaultLauncher = launchersById[defaultLauncherId];

  // Launcher field

  const launcherOptions = launchers.map(({ id, name }) => ({
    value: id,
    label: name,
  }));

  // Version field

  const studiesById = getStudiesById(store.getState());
  const studies = studyIds.map((id) => studiesById[id]).filter(Boolean);
  const maxStudyVersion = Math.max(...studies.map((study) => Number(study.version)));

  const getVersionOptionsForLauncher = (launcherId: Launcher["id"]) => {
    const versions = launchersById[launcherId].versions;

    return versions
      .filter((version) => Number(version) >= maxStudyVersion)
      .map((version) => ({
        value: version,
        label: displayVersionName(version),
      }));
  };

  // Configuration field

  const solverPresets = await getSolverPresets();
  const configurationOptions = solverPresets.map(({ id, name }) => ({ value: id, label: name }));

  // Output field

  const isSingleStudy = studyIds.length === 1;
  const studyOutputs = isSingleStudy ? await getStudyOutputs(studyIds[0]) : [];
  const outputOptions = studyOutputs.map(({ name }) => name);

  return {
    name: "",
    autoUnzip: true,
    version: maxStudyVersion.toString(),
    configuration: configurationOptions[0]?.value,
    otherOptions: "",
    xpansion: false,
    adequacyCriterion: false,
    sensitivityMode: false,
    output: "",
    launcher: defaultLauncher.id,
    nbCores: defaultLauncher.nbCores.default,
    timeLimit: defaultLauncher.timeLimit.default,
    // TODO: Replace by implementing metadata in `Form` if it's not implemented yet by react-hook-form
    // https://github.com/react-hook-form/react-hook-form/issues/13036
    _data: {
      launchersById,
      launcherOptions,
      getVersionOptionsForLauncher,
      configurationOptions,
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
