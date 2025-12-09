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
import { getSolverPresets } from "@/services/api/launcher/solverPresets";
import { getLaunchersConfig, getStudyOutputs, type Launcher } from "@/services/api/study";
import type { StudyMetadata } from "@/types/types";
import * as R from "ramda";

export const XPRESS_OPTION = "xpress" as const;

// TODO: utils to formalize versions format from API
// Convert version format from '[major].[minor]' to number '[major][minor][patch]'
const formalizeVersion = (version: string): number => {
  return Number(version.replace(".", "").padEnd(3, "0"));
};

export const getDefaultValues = async (studyIds: Array<StudyMetadata["id"]>) => {
  const { launchers, defaultLauncher: defaultLauncherId } = await getLaunchersConfig();

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
  // The version format of `study.version` is '[major][minor][patch]' as string
  const maxStudyVersion = Math.max(...studies.map((study) => Number(study.version)));

  const getVersionOptionsForLauncher = (launcherId: Launcher["id"]) => {
    const versions = launchersById[launcherId].versions;
    return versions.filter((version) => formalizeVersion(version) >= maxStudyVersion);
  };

  const defaultVersion = getVersionOptionsForLauncher(defaultLauncher.id)[0] || "";

  // Configuration field

  const solverPresets = await getSolverPresets();
  const solverPresetsById = R.indexBy(R.prop("id"), solverPresets);

  const getConfigurationOptionsForVersion = (version: string) => {
    const formalizedVersion = formalizeVersion(version);

    return solverPresets
      .filter(({ minAntaresVersion, maxAntaresVersion }) => {
        const formalizedMinVersion = minAntaresVersion ? formalizeVersion(minAntaresVersion) : 0;
        const formalizedMaxVersion = maxAntaresVersion
          ? formalizeVersion(maxAntaresVersion)
          : Infinity;

        return (
          formalizedVersion >= formalizedMinVersion && formalizedVersion <= formalizedMaxVersion
        );
      })
      .map(({ id, name }) => ({ value: id, label: name }));
  };

  const defaultConfiguration = getConfigurationOptionsForVersion(defaultVersion)[0]?.value || "";

  // Output field

  const isSingleStudy = studyIds.length === 1;
  const studyOutputs = isSingleStudy ? await getStudyOutputs(studyIds[0]) : [];
  const outputOptions = studyOutputs.map(({ name }) => name);

  return {
    name: "",
    autoUnzip: true,
    version: defaultVersion,
    configuration: defaultConfiguration,
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
      solverPresetsById,
      launcherOptions,
      getVersionOptionsForLauncher,
      getConfigurationOptionsForVersion,
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
  return formalizeVersion(version) >= 830;
};
