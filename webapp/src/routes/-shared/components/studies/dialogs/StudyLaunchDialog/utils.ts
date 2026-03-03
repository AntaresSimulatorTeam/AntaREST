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

import { getStudiesById } from "@/redux/selectors";
import store from "@/redux/store";
import { getLaunchersConfig } from "@/services/api/launcher/index";
import { getSolverPresets } from "@/services/api/launcher/solverPresets";
import type { LauncherDTO } from "@/services/api/launcher/types";
import { getStudyOutputs } from "@/services/api/study";
import type { StudyMetadata } from "@/types/types";
import {
  getHighestVersion,
  getSemanticVersionOptions,
  MAX_SEMVER,
  ZERO_SEMVER,
} from "@/utils/versionUtils";
import * as R from "ramda";
import semver from "semver";

export const XPRESS_OPTION = "xpress" as const;

export async function getDefaultValues(studyIds: Array<StudyMetadata["id"]>) {
  const { launchers, defaultLauncher: defaultLauncherId } = await getLaunchersConfig();

  const launchersById = R.indexBy(R.prop("id"), launchers);
  const defaultLauncher = launchersById[defaultLauncherId];

  /* Launcher field */

  const launcherOptions = launchers.map(({ id, name }) => ({
    value: id,
    label: name,
  }));

  /* Version field */

  const studiesById = getStudiesById(store.getState());
  const studies = studyIds.map((id) => studiesById[id]).filter(Boolean);
  const highestStudyVersion = getHighestVersion(studies.map(({ version }) => version));

  const getVersionOptionsForLauncher = (launcherId: LauncherDTO["id"]) => {
    const { versions } = launchersById[launcherId];

    if (!highestStudyVersion) {
      return [];
    }

    return getSemanticVersionOptions(
      versions.filter((version) => semver.gte(version, highestStudyVersion)),
    );
  };

  const defaultVersion = getVersionOptionsForLauncher(defaultLauncher.id)[0]?.value || "";

  /* Configuration field */

  const solverPresets = await getSolverPresets();
  const solverPresetsById = R.indexBy(R.prop("id"), solverPresets);

  const getConfigurationOptionsForVersion = (version: string) => {
    if (!version) {
      return [];
    }

    return solverPresets
      .filter(({ minAntaresVersion, maxAntaresVersion }) => {
        return (
          semver.gte(version, minAntaresVersion || ZERO_SEMVER) &&
          semver.lte(version, maxAntaresVersion || MAX_SEMVER)
        );
      })
      .map(({ id, name }) => ({ value: id, label: name }));
  };

  const defaultConfiguration = getConfigurationOptionsForVersion(defaultVersion)[0]?.value || "";

  /* Output field */

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
}

export type FormValues = Awaited<ReturnType<typeof getDefaultValues>>;

export function otherOptionsToArray(otherOptions: string): string[] {
  return otherOptions.trim() === "" ? [] : otherOptions.split(/\s+/);
}

export function isXpressAvailableForVersion(version: FormValues["version"]) {
  return semver.gte(version, "8.3.0");
}
